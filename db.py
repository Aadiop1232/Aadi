# db.py
import sqlite3
import json

DATABASE = "bot.db"

def init_db():
    """
    Initialize the database with all necessary tables.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table: stores Telegram ID, username, join date, points, referrals, banned flag, pending_referrer
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            username TEXT,
            join_date TEXT,
            points INTEGER DEFAULT 20,
            referrals INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            pending_referrer TEXT
        )
    ''')
    
    # Referrals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            user_id TEXT,
            referred_id TEXT,
            PRIMARY KEY (user_id, referred_id)
        )
    ''')
    
    # Platforms table: platform name and JSON-encoded stock
    c.execute('''
        CREATE TABLE IF NOT EXISTS platforms (
            platform_name TEXT PRIMARY KEY,
            stock TEXT
        )
    ''')

    # Reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            review TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Admin logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Channels table
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_link TEXT
        )
    ''')

    # Admins table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            role TEXT,
            banned INTEGER DEFAULT 0
        )
    ''')

    # Keys table: stores key details, type, points, and whether it has been claimed.
    c.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            type TEXT,
            points INTEGER,
            claimed INTEGER DEFAULT 0,
            claimed_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def add_user(telegram_id, username, join_date, pending_referrer=None):
    """
    Adds a new user to the database if they do not already exist.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id, username, join_date, pending_referrer) VALUES (?, ?, ?, ?)",
              (telegram_id, username, join_date, pending_referrer))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    """
    Retrieves a user from the database by their telegram_id.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user_pending_referral(telegram_id, pending_referrer):
    """
    Updates the pending referral for a user.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET pending_referrer=? WHERE telegram_id=?", (pending_referrer, telegram_id))
    conn.commit()
    conn.close()

def clear_pending_referral(telegram_id):
    """
    Clears the pending referral for a user.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET pending_referrer=NULL WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

def add_referral(referrer_id, referred_id):
    """
    Adds a referral entry in the database and updates points for the referrer.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM referrals WHERE referred_id=?", (referred_id,))
    if c.fetchone():
        conn.close()
        return
    c.execute("INSERT INTO referrals (user_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
    c.execute("UPDATE users SET points = points + 4, referrals = referrals + 1 WHERE telegram_id=?", (referrer_id,))
    conn.commit()
    conn.close()

def add_review(user_id, review):
    """
    Adds a review from a user to the database.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id, review) VALUES (?, ?)", (user_id, review))
    conn.commit()
    conn.close()

def log_admin_action(admin_id, action):
    """
    Logs an action taken by an admin in the admin logs table.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO admin_logs (admin_id, action) VALUES (?, ?)", (admin_id, action))
    conn.commit()
    conn.close()

def get_key(key):
    """
    Retrieves a specific key from the database.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT key, type, points, claimed FROM keys WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    return result

def add_key(key, key_type, points):
    """
    Adds a new key (normal or premium) to the keys table.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO keys (key, type, points, claimed) VALUES (?, ?, ?, ?)", 
              (key, key_type, points, 0))
    conn.commit()
    conn.close()

def claim_key_in_db(key, telegram_id):
    """
    Claims a key for the user and adds the points to their account.
    """
    conn = sqlite3.connect(DATABASE)
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
    c.execute("UPDATE keys SET claimed=1, claimed_by=? WHERE key=?", (telegram_id, key))
    c.execute("UPDATE users SET points = points + ? WHERE telegram_id=?", (points, telegram_id))
    conn.commit()
    conn.close()
    return f"Key redeemed successfully. You've been awarded {points} points."

def update_user_points(telegram_id, points):
    """
    Updates the points for a specific user.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET points=? WHERE telegram_id=?", (points, telegram_id))
    conn.commit()
    conn.close()

def get_platforms():
    """
    Retrieves all platforms from the platforms table.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT platform_name FROM platforms")
    platforms = [row[0] for row in c.fetchall()]
    conn.close()
    return platforms

def get_stock_for_platform(platform_name):
    """
    Retrieves the stock of accounts for a specific platform.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT stock FROM platforms WHERE platform_name=?", (platform_name,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])  # Convert JSON string back into a list of accounts
        except Exception:
            return []
    return []

def update_stock_for_platform(platform_name, stock):
    """
    Updates the stock for a given platform.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE platforms SET stock=? WHERE platform_name=?", (json.dumps(stock), platform_name))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized!")
    
