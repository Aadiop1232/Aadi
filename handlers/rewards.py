# handlers/rewards.py
import telebot
from telebot import types
import sqlite3
import json
import random
from db import DATABASE, update_user_points, get_user

def get_db_connection():
    return sqlite3.connect(DATABASE)

def get_platforms():
    """ Fetch all available platforms from the database. """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT platform_name FROM platforms")
    platforms = [row[0] for row in c.fetchall()]
    conn.close()
    return platforms

def get_stock_for_platform(platform_name):
    """ Get the stock of accounts for a given platform. """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT stock FROM platforms WHERE platform_name=?", (platform_name,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])  # Return as a list of accounts
        except Exception:
            return []
    return []

def update_stock_for_platform(platform_name, stock):
    """ Update the stock of accounts for a given platform. """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE platforms SET stock=? WHERE platform_name=?", (json.dumps(stock), platform_name))
    conn.commit()
    conn.close()

def send_rewards_menu(bot, message):
    """ Send the rewards menu to the user. """
    platforms = get_platforms()
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Check if there are platforms available
    if not platforms:
        bot.send_message(message.chat.id, "😢 <b>No platforms available at the moment.</b>", parse_mode="HTML")
        return

    # Add buttons for each platform
    for platform in platforms:
        markup.add(types.InlineKeyboardButton(f"📺 {platform}", callback_data=f"reward_{platform}"))
    
    # Add a back button to main menu
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_main"))

    bot.send_message(message.chat.id, "<b>🎯 Available Platforms 🎯</b>", parse_mode="HTML", reply_markup=markup)

def handle_platform_selection(bot, call, platform):
    """ Handle the platform selection to show available accounts. """
    stock = get_stock_for_platform(platform)

    if stock:
        text = f"<b>📺 {platform}</b>:\n✅ <b>{len(stock)} accounts available!</b>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🎁 Claim Account", callback_data=f"claim_{platform}"))
    else:
        text = f"<b>📺 {platform}</b>:\n😞 No accounts available at the moment."
        markup = types.InlineKeyboardMarkup()
    
    # Add a back button to rewards menu
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_rewards"))
    
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)

def claim_account(bot, call, platform):
    """ Handle the account claiming system, deduct points, and update stock. """
    user_id = str(call.from_user.id)
    user = get_user(user_id)

    if user is None:
        bot.answer_callback_query(call.id, "User not found.")
        return

    # Get current points of the user
    try:
        current_points = int(float(user[4]))  # Points are stored as integer or float
    except Exception:
        bot.answer_callback_query(call.id, "Error reading your points.")
        return

    # Check if user has enough points to claim an account
    if current_points < 2:
        bot.answer_callback_query(call.id, "Insufficient points (each account costs 2 points). Earn more by referring or redeeming a key.")
        return

    # Get the stock for the platform
    stock = get_stock_for_platform(platform)
    if not stock:
        bot.answer_callback_query(call.id, "😞 No accounts available.")
        return

    # Randomly select an account from the available stock
    account = stock.pop(random.randint(0, len(stock) - 1))

    # Deduct points from the user's balance
    new_points = current_points - 2
    update_user_points(user_id, new_points)

    # Update the stock for the platform
    update_stock_for_platform(platform, stock)

    # Inform the user and send the account details
    bot.answer_callback_query(call.id, "🎉 Account claimed!")
    bot.send_message(call.message.chat.id,
                     f"<b>Your account for {platform}:</b>\n<code>{account}</code>\nRemaining points: {new_points}",
                     parse_mode="HTML")

    # Optionally, notify admins about the claim (this can be added in the future)
    # bot.send_message(admin_id, f"User {user[2]} has claimed an account for {platform}.")
    
