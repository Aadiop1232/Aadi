# handlers/main_menu.py
import telebot
from telebot import types
from handlers.admin import is_admin

def send_main_menu(bot, message):
    """
    Sends the main menu to the user.
    The "Admin Panel" button is always visible for admins, even after navigating to the admin panel.
    """
    user_obj = message.from_user
    telegram_id = str(user_obj.id)
    
    # Check if the user is an admin
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_rewards = types.InlineKeyboardButton("💳 Rewards", callback_data="menu_rewards")
    btn_account = types.InlineKeyboardButton("👤 Account Info", callback_data="menu_account")
    btn_referral = types.InlineKeyboardButton("🔗 Referral System", callback_data="menu_referral")
    btn_review = types.InlineKeyboardButton("💬 Review", callback_data="menu_review")
    markup.add(btn_rewards, btn_account, btn_referral, btn_review)

    # Always show the "Admin Panel" button if the user is an admin
    if is_admin(user_obj):
        btn_admin = types.InlineKeyboardButton("🛠 Admin Panel", callback_data="menu_admin")
        markup.add(btn_admin)

    # Sending main menu with the options
    bot.send_message(message.chat.id, "<b>📋 Main Menu 📋</b>\nPlease choose an option:", parse_mode="HTML", reply_markup=markup)

def send_back_to_main_menu(bot, message):
    """
    Sends the back button to go back to the main menu
    """
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
    markup.add(back_button)
    bot.send_message(message.chat.id, "Returning to main menu...", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def callback_back_main(call):
    """
    Callback for when a user clicks the back button to return to the main menu.
    The "Admin Panel" button will still be visible for admins.
    """
    send_main_menu(bot, call.message)
    
