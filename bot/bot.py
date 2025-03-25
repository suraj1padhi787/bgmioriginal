from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import requests
import hashlib
import time
import random

# Telegram Bot Token and Admin Chat ID
TOKEN = '7718773479:AAE9AAdx0W2pWq6guVzF2lM5oySaY-AZyGc'
ADMIN_CHAT_ID = '6148224523'

# Payment Gateway Configuration
API_KEY = '46460da2747c4f639d3f3681a42edec8'
MCH_ID = '100789053'
PAYMENT_URL = 'https://api.watchglbpay.com/pay/web'
CALLBACK_URL = 'https://yourdomain.com/callback'
REDIRECT_URL = 'https://yourdomain.com/success'


# Hack Categories and Pricing with Descriptions
HACKS = {
    "Android Root Hacks": {
        "Sharpshooter": {"Week": 700, "Month": 1300, "Description": "Sharpshooter is designed for users who want accurate and powerful aiming capabilities in BGMI, allowing precise shots even from a distance. Join main Group @SharpShooter7872"},
        "Titan": {"Week": 700, "Month": 1300, "Description": "Titan provides players with enhanced features such as speed hacks and teleportation, making it ideal for aggressive gameplay. Join main Group @Titan7872" }
        
    },
    "Android Non-Root Hacks": {
        "Titan": {"Week": 800, "Month": 1400, "Description": "Titan (Non-root) is a less intrusive hack offering speed boosts and combat advantages without needing to root the device.Join main Group Join main Group @Titan7872"},
        "Vision": {"Week": 800, "Month": 1400, "Description": "Vision enhances your visibility in the game, allowing you to spot enemies through walls and other obstacles. Join main Group @LithalAndVision"},
        "Lethal": {"Week": 800, "Month": 1400, "Description": "Lethal offers superior combat features like rapid fire and high accuracy for maximum domination in BGMI. Join main Group @LithalAndVision"}
    },
    "iOS Hacks": {
        "WinIOS": {"Week": 900, "Month": 1600, "Description": "WinIOS brings a competitive edge for iOS users, unlocking various cheats to make your gameplay smoother and more powerful. @WinIos7872"},
        "iOS Zero": {"Week": 900, "Month": 1600, "Description": "iOS Zero offers a unique set of features, including wallhacks and aimbots, to give iOS players an advantage in BGMI. Join main Group @IosZero7872"},
        "Shoot 360": {"Week": 900, "Month": 1600, "Description": "Shoot 360 offers dynamic 360-degree shooting, allowing for instant reaction to enemies surrounding you."}
    },
    "PC Hacks": {
        "PC Titan": {"Week": 1000, "Month": 1800, "Description": "PC Titan is a robust hack for PC gamers, providing features like rapid movement and increased damage to outplay your opponents.Join main Group @pc7872"}
    },
    "Server Freeze Hack": {
        "Freeze Server": {"One-Time": 2000, "Description": "Server Freeze allows you to crash game servers, making them temporarily unusable, ideal for causing disruption during competitive matches. Join main Group @ServerFreeze7872"}
    }
}

# States
CATEGORY, HACK, VALIDITY = range(3)

# Generate MD5 Signature
def generate_sign(params, secret_key):
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params) + f"&key={secret_key}"
    return hashlib.md5(sign_str.encode()).hexdigest()

# Generate Payment Link
def generate_payment(hack_name, amount):
    order_id = "BGMI" + str(random.randint(10000, 999999))
    order_date = time.strftime('%Y-%m-%d %H:%M:%S')

    params = {
        'version': '1.0',
        'mch_id': MCH_ID,
        'mch_order_no': order_id,
        'pay_type': '101',
        'trade_amount': amount,
        'order_date': order_date,
        'goods_name': hack_name,
        'notify_url': CALLBACK_URL,
        'page_url': REDIRECT_URL,
        'mch_return_msg': hack_name,
    }

    sign = generate_sign(params, API_KEY)
    params['sign'] = sign
    params['sign_type'] = "MD5"

    try:
        response = requests.post(PAYMENT_URL, data=params)
        response_data = response.json()
        if response_data.get('tradeResult') == '1' and 'payInfo' in response_data:
            return response_data['payInfo']
        else:
            print("Payment Link Generation Failed:", response_data)
            return None
    except Exception as e:
        print("Error generating payment link:", e)
        return None

# Back Function
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'category' in context.user_data:
        del context.user_data['category']
    if 'hack' in context.user_data:
        del context.user_data['hack']
    if 'validity' in context.user_data:
        del context.user_data['validity']

    # Go back to category selection
    await update.message.reply_text("Going back to the main menu. Select a hack category:", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(category) for category in HACKS.keys()]], one_time_keyboard=True, resize_keyboard=True))
    return CATEGORY

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(category)] for category in HACKS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Select a hack category:", reply_markup=reply_markup)
    return CATEGORY

# Update for all steps to include "Back" button
async def select_hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.strip()
    if category not in HACKS:
        await update.message.reply_text("Invalid category. Please select again.")
        return CATEGORY
    context.user_data['category'] = category
    keyboard = [[KeyboardButton(hack)] for hack in HACKS[category]] + [[KeyboardButton("🔙 Back")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Select a hack:", reply_markup=reply_markup)
    return HACK

async def select_validity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await go_back(update, context)
    
    hack = update.message.text.strip()
    category = context.user_data.get('category')
    if hack not in HACKS[category]:
        await update.message.reply_text("Invalid hack. Please select again.")
        return HACK
    context.user_data['hack'] = hack
    description = HACKS[category][hack]["Description"]
    keyboard = [[KeyboardButton(f"{validity} - ₹{price}")] for validity, price in HACKS[category][hack].items() if validity != "Description"]
    keyboard.append([KeyboardButton("🔙 Back")])
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Description: {description}\n\nSelect validity:", reply_markup=reply_markup)
    return VALIDITY

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await go_back(update, context)
    
    validity = update.message.text.strip()
    hack = context.user_data['hack']
    category = context.user_data['category']
    
    for period, amount in HACKS[category][hack].items():
        if period in validity:
            selected_amount = amount
            break
    else:
        await update.message.reply_text("Invalid validity. Please select again.")
        return VALIDITY
    
    payment_link = generate_payment(hack, selected_amount)
    
    if payment_link:
        keyboard = [[InlineKeyboardButton("💳 Pay Now", url=payment_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = (
            f"*You've selected {hack} ({validity}).*\n"
            f"*💰 Total: ₹{selected_amount}*\n\n"
            "*Click below to complete your payment.*"
        )
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        await update.message.reply_text("To explore more, enter /start")
        admin_message = (
            f"🚨 *New Purchase Request* 🚨\n\n"
            f"👤 *User:* `{update.message.from_user.username or 'Unknown'}` (ID: `{update.message.from_user.id}`)\n"
            f"🎮 *Hack:* `{hack}`\n"
            f"📅 *Validity:* `{validity}`\n"
            f"💰 *Amount:* ₹{selected_amount}\n"
            f"🔗 *Payment Link:* {payment_link}"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
    else:
        await update.message.reply_text("Payment link generation failed. Please try again later.")

    return ConversationHandler.END

# Main Function
def main():
    app = Application.builder().token(TOKEN).build()
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_hack)],
            HACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_validity)],
            VALIDITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_payment)]
        },
        fallbacks=[],
    )
    app.add_handler(conversation_handler)
    app.run_polling()

if __name__ == '__main__':
    main()

if __name__ == "__main__":
    main()

