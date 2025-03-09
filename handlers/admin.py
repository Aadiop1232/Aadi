# handlers/admin.py
import telebot
from telebot import types
import sqlite3
import random, string, json, re
import config
from db import DATABASE, log_admin_action, add_key

def get_db_connection():
    return sqlite3.connect(getattr(config, "DATABASE", "bot.db"))

###############################
# PLATFORM MANAGEMENT FUNCTIONS
###############################
def add_platform(platform_name):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO platforms (platform_name, stock) VALUES (?, ?)", (platform_name, json.dumps([])))
        conn.commit()
    except Exception as e:
        conn.close()
        return str(e)
    conn.close()
    return None

def remove_platform(platform_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM platforms WHERE platform_name=?", (platform_name,))
    conn.commit()
    conn.close()

def get_platforms():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT platform_name FROM platforms")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_stock_to_platform(platform_name, accounts):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT stock FROM platforms WHERE platform_name=?", (platform_name,))
    row = c.fetchone()
    if row and row[0]:
        stock = json.loads(row[0])
    else:
        stock = []
    stock.extend(accounts)
    c.execute("UPDATE platforms SET stock=? WHERE platform_name=?", (json.dumps(stock), platform_name))
    conn.commit()
    conn.close()

###############################
# CHANNEL MANAGEMENT FUNCTIONS
###############################
def get_channels():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, channel_link FROM channels")
    rows = c.fetchall()
    conn.close()
    return rows

def add_channel(channel_link):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO channels (channel_link) VALUES (?)", (channel_link,))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()

###############################
# ADMINS MANAGEMENT FUNCTIONS
###############################
def get_admins():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_id, username, role, banned FROM admins")
    rows = c.fetchall()
    conn.close()
    return rows

def add_admin(user_id, username, role="admin"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO admins (user_id, username, role, banned) VALUES (?, ?, ?, 0)",
              (str(user_id), username, role))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (str(user_id),))
    conn.commit()
    conn.close()

def ban_admin(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE admins SET banned=1 WHERE user_id=?", (str(user_id),))
    conn.commit()
    conn.close()

def unban_admin(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE admins SET banned=0 WHERE user_id=?", (str(user_id),))
    conn.commit()
    conn.close()

###############################
# USERS MANAGEMENT FUNCTIONS
###############################
def get_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT telegram_id, username, banned FROM users")
    rows = c.fetchall()
    conn.close()
    return rows

def ban_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET banned=1 WHERE telegram_id=?", (str(user_id),))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET banned=0 WHERE telegram_id=?", (str(user_id),))
    conn.commit()
    conn.close()

###############################
# KEYS MANAGEMENT FUNCTIONS
###############################
def generate_normal_key():
    return "NKEY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def generate_premium_key():
    return "PKEY-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def add_key(key, key_type, points):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, type, points, claimed) VALUES (?, ?, ?, 0)", (key, key_type, points))
    conn.commit()
    conn.close()

def get_keys():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, type, points, claimed, claimed_by FROM keys")
    rows = c.fetchall()
    conn.close()
    return rows

def claim_key_in_db(key, user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT claimed, type, points FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return "Key not found."
    if row[0] != 0:
        conn.close()
        return "Key already claimed."
    points = row[2]
    c.execute("UPDATE keys SET claimed=1, claimed_by=? WHERE key=?", (user_id, key))
    c.execute("UPDATE users SET points = points + ? WHERE telegram_id=?", (points, user_id))
    conn.commit()
    conn.close()
    return f"Key redeemed successfully. You've been awarded {points} points."

###############################
# ADMIN PANEL HANDLERS & SECURITY
###############################
def is_owner(user_or_id):
    if user_or_id is None:
        return False
    try:
        tid = str(user_or_id.id)
        uname = (user_or_id.username or "").lower()
    except AttributeError:
        tid = str(user_or_id)
        uname = ""
    owners = [str(x).lower() for x in config.OWNERS]
    if tid.lower() in owners or (uname and uname in owners):
        print(f"DEBUG is_owner: {tid} or {uname} recognized as owner.")
        return True
    return False

def is_admin(user_or_id):
    if is_owner(user_or_id):
        return True
    if user_or_id is None:
        return False
    try:
        tid = str(user_or_id.id)
        uname = (user_or_id.username or "").lower()
    except AttributeError:
        tid = str(user_or_id)
        uname = ""
    admins = [str(x).lower() for x in config.ADMINS]
    if tid.lower() in admins or (uname and uname in admins):
        print(f"DEBUG is_admin: {tid} or {uname} recognized as admin.")
        return True
    return False

def send_admin_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_owner(message.from_user):
        markup.add(
            types.InlineKeyboardButton("📺 Platform Mgmt", callback_data="admin_platform"),
            types.InlineKeyboardButton("📈 Stock Mgmt", callback_data="admin_stock"),
            types.InlineKeyboardButton("🔗 Channel Mgmt", callback_data="admin_channel"),
            types.InlineKeyboardButton("👥 Admin Mgmt", callback_data="admin_manage"),
            types.InlineKeyboardButton("➕ Add Admin", callback_data="admin_add")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("📺 Platform Mgmt", callback_data="admin_platform"),
            types.InlineKeyboardButton("📈 Stock Mgmt", callback_data="admin_stock"),
            types.InlineKeyboardButton("👤 User Mgmt", callback_data="admin_users")
        )
    markup.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_main"))
    bot.send_message(message.chat.id, "<b>🛠 Admin Panel</b> 🛠", parse_mode="HTML", reply_markup=markup)

###############################
# KEY GENERATION AND ADMIN LOGGING
###############################
def handle_admin_add_key(bot, call):
    # Handle admin key generation, logging, and notification
    key_type = call.data.split("_")[1]
    qty = int(call.data.split("_")[2])
    generated = []

    if key_type == "normal":
        for _ in range(qty):
            key = generate_normal_key()
            add_key(key, "normal", 15)
            generated.append(key)
    elif key_type == "premium":
        for _ in range(qty):
            key = generate_premium_key()
            add_key(key, "premium", 35)
            generated.append(key)

    action = f"Generated {len(generated)} {key_type} keys"
    log_admin_action(call.from_user.id, action)

    # Notify the owners about the key generation
    bot = telebot.TeleBot(config.TOKEN)
    for owner in config.OWNERS:
        bot.send_message(owner, f"Admin {call.from_user.username} has generated keys: \n" + "\n".join(generated))

    bot.send_message(call.message.chat.id, f"Generated keys:\n" + "\n".join(generated))

###############################
# CALLBACK ROUTER
###############################
def admin_callback_handler(bot, call):
    data = call.data
    if not is_admin(call.from_user):
        bot.answer_callback_query(call.id, "Access prohibited.")
        return
    if data == "admin_platform":
        handle_admin_platform(bot, call)
    elif data == "admin_platform_add":
        handle_admin_platform_add(bot, call)
    elif data == "admin_platform_remove":
        handle_admin_platform_remove(bot, call)
    elif data.startswith("admin_platform_rm_"):
        platform = data.split("admin_platform_rm_")[1]
        handle_admin_platform_rm(bot, call, platform)
    elif data == "admin_stock":
        handle_admin_stock(bot, call)
    elif data.startswith("admin_stock_"):
        platform = data.split("admin_stock_")[1]
        handle_admin_stock_platform(bot, call, platform)
    elif data == "admin_channel":
        handle_admin_channel(bot, call)
    elif data == "admin_channel_add":
        handle_admin_channel_add(bot, call)
    elif data == "admin_channel_remove":
        handle_admin_channel_remove(bot, call)
    elif data.startswith("admin_channel_rm_"):
        channel_id = data.split("admin_channel_rm_")[1]
        handle_admin_channel_rm(bot, call, channel_id)
    elif data == "admin_manage":
        handle_admin_manage(bot, call)
    elif data == "admin_list":
        handle_admin_list(bot, call)
    elif data == "admin_ban_unban":
        handle_admin_ban_unban(bot, call)
    elif data == "admin_remove":
        handle_admin_remove(bot, call)
    elif data == "admin_add":
        handle_admin_add(bot, call)
    elif data == "admin_add_owner":
        handle_admin_add_owner(bot, call)
    else:
        bot.answer_callback_query(call.id, "❓ Unknown admin command.")
    
