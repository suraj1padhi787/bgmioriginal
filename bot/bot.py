import logging
import os
import random
import re
import time
import hashlib
import requests
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8043793382:AAF3huUaOwSKcY8xLE7Q4A-28HHYOWT4k78")
ADMIN_IDS = [5893249491]

# Payment Gateway Config
API_KEY = '46460da2747c4f639d3f3681a42edec8'
MCH_ID = '100789053'
PAYMENT_URL = 'https://api.watchglbpay.com/pay/web'
CALLBACK_URL = 'https://yourdomain.com/callback'
REDIRECT_URL = 'https://yourdomain.com/success'

# ================ Logging ================
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ================ Data Storage ============
user_queries = {}
user_orders = {}
registered_users = set()

# ================ Plan Pricing ============
hack_plans = {
    "day": {"name": "Day Plan", "amount": 200},
    "week": {"name": "Weekly Plan", "amount": 700},
    "month": {"name": "Monthly Plan", "amount": 1500},
    "premium": {"name": "Premium Plan", "amount": 5000},  # Premium plan for exclusive features
}

categories = {
    "🔓 Root Hacks": {
        "Sharpshooter": "Precision aimbot with adjustable sensitivity. Great for players looking for accuracy without compromise. Join main group @SHARPSHOOTER7872",
        "Titan": "Wallhack and ESP (Extra Sensory Perception) to see opponents and items through walls. join main group @TITAN7872",
        "King Root": "Full control over the game environment with root access, ensuring unbeatable advantages. Join main group @KINGMOD7872",
        "Dead Eye": "Silent aim with auto-targeting, making your shots deadly accurate without detection. Join main group @DEADEYE7872"
    },
    "🔒 Non-Root Hacks": {
        "Illusion": "Undetectable ESP with full visibility of enemies. Perfect for those who need stealth in their gameplay. jOIN MAIN GROUP @ILLUSION7872",
        "King Mod": "Enhances your movement speed and accuracy, combined with auto-headshot features.Join main group @KINGMOD7872",
        "Game Nova": "Completely customizable mod pack with recoil control and anti-bullet mechanics. Join main group @KINGNOVA7872",
        "Vision": "Radar hack and night vision mode for seeing your enemies in total darkness. Join main group @VISION7872"
    },
    "🍏 iOS Hacks": {
        "WiniOS": "Specialized aimbot with enhanced targeting features for iOS users, works smoothly on the platform. Join main group @WINIOS7872",
        "King iOS": "Full ESP and aim assist designed specifically for iOS devices, providing a competitive edge. Join main group @KINGIOS7872",
        "Shoot 360": "Full ESP and aim assist designed specifically for iOS devices, providing a competitive edge. Join main group @SHOOT3607872"
    },
    "🧊 Server Freeze": {
        "Server Freeze Hack": "Temporarily freezes the server, causing massive lag for enemies, disrupting their gameplay. Join main group @SERVERFREEZE7872"
    }
}

# ================ Payment Generation ===========
def generate_sign(params, secret_key):
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params) + f"&key={secret_key}"
    return hashlib.md5(sign_str.encode()).hexdigest()

def generate_payment_link(custom_name, user_id, amount):
    order_id = f"ORDER{user_id}{random.randint(1000,9999)}"
    order_date = time.strftime('%Y-%m-%d %H:%M:%S')
    params = {
        'version': '1.0',
        'mch_id': MCH_ID,
        'mch_order_no': order_id,
        'pay_type': '101',
        'trade_amount': amount,
        'order_date': order_date,
        'goods_name': custom_name,
        'notify_url': CALLBACK_URL,
        'page_url': REDIRECT_URL,
        'mch_return_msg': str(user_id),
    }
    sign = generate_sign(params, API_KEY)
    params['sign'] = sign
    params['sign_type'] = 'MD5'

    try:
        response = requests.post(PAYMENT_URL, data=params)
        data = response.json()
        if data.get("tradeResult") == "1" and "payInfo" in data:
            return data["payInfo"]
        else:
            logger.error(f"Payment API Error: {data}")
            return None
    except Exception as e:
        logger.error(f"Payment Link Generation Error: {e}")
        return None

# ================ Start Handler ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    registered_users.add(user.id)
    keyboard = []
    row = []
    for i, cat in enumerate(categories.keys(), 1):
        row.append(KeyboardButton(cat))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("📩 Contact Us")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome to *Hacks Bot*\n\nSelect a category:", reply_markup=reply_markup, parse_mode='Markdown')

# ================ Message Handler ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user

    # ✅ Auto-detect UTR (12-digit)
    if re.match(r"^\d{12}$", text):
        if user_orders.get(user.id):
            hack, plan, _ = user_orders[user.id][-1]
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    admin_id,
                    f"✅ Payment UTR Received\n👤 {user.full_name} (ID: {user.id})\n📝 Username: @{user.username}\n🔧 Hack: {hack}\n📆 Plan: {plan}\n🧾 UTR: {text}"
                )
            await update.message.reply_text("✅ UTR received. Admin will verify shortly.")
        else:
            await update.message.reply_text("❗ No recent order found. Please select a hack and plan first.")
        return

    # 📩 Contact message
    if context.user_data.get("awaiting_query"):
        for admin_id in ADMIN_IDS:
            sent = await context.bot.send_message(admin_id, f"📩 Query from {user.full_name} (ID: {user.id}) (@{user.username}):\n{text}")
            user_queries[sent.message_id] = user.id
        await update.message.reply_text("✅ Your query has been sent to admin.")
        context.user_data["awaiting_query"] = False
        return

    # Category selection
    if text in categories:
        context.user_data["selected_category"] = text
        hacks = categories[text]
        keyboard = []
        row = []
        for i, hack in enumerate(hacks.keys(), 1):
            row.append(KeyboardButton(hack))
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([KeyboardButton("⬅ Back")])
        await update.message.reply_text(f"🔍 {text}\nSelect a hack:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    # Hack selected
    elif text in [hack for sublist in categories.values() for hack in sublist.keys()]:
        context.user_data["selected_hack"] = text
        hack_description = ""
        for category in categories.values():
            if text in category:
                hack_description = category[text]
                break
        keyboard = [
            [KeyboardButton("🗓 Week Plan")],
            [KeyboardButton("📆 Month Plan")],
            [KeyboardButton("💎 Premium Plan")],
            [KeyboardButton("⬅ Back")]
        ]
        await update.message.reply_text(
            f"🎯 *{text}*\n\nDescription: {hack_description}\n\nChoose a plan:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='Markdown'
        )

    # Plan selection
    elif text.lower() in ["📅 day plan", "🗓 week plan", "📆 month plan", "💎 premium plan"]:
        hack_name = context.user_data.get("selected_hack")
        plan_map = {"📅 day plan": "day", "🗓 week plan": "week", "📆 month plan": "month", "💎 premium plan": "premium"}
        plan_key = plan_map.get(text.lower())
        plan = hack_plans.get(plan_key)
        payment_url = generate_payment_link(f"{hack_name} - {plan['name']}", user.id, plan["amount"])
        if payment_url:
            pay_btn = InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=payment_url)]])
            await update.message.reply_text(
                f"✅ *Hack:* {hack_name}\n📆 *Plan:* {plan['name']}\n💰 ₹{plan['amount']}\n\n📤 After payment, send your *screenshot or UTR* here.",
                reply_markup=pay_btn, parse_mode='Markdown')
            user_orders.setdefault(user.id, []).append((hack_name, plan['name'], "Pending"))
        else:
            await update.message.reply_text("❌ Payment link failed. Try again later.")

    elif text == "⬅ Back":
        await start(update, context)

    elif "contact" in text.lower():
        context.user_data["awaiting_query"] = True
        await update.message.reply_text("📨 Please type your message. Admin will reply soon.")

    else:
        await update.message.reply_text("❗ Invalid option. Use /start to begin again.")

# ================ Screenshot Handler ============
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_orders.get(user.id):
        hack, plan, _ = user_orders[user.id][-1]
        caption = f"📸 Payment Screenshot\n👤 {user.full_name} (ID: {user.id}) (@{user.username})\n🔧 Hack: {hack}\n📆 Plan: {plan}"
        for admin_id in ADMIN_IDS:
            await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=caption)
        await update.message.reply_text("✅ Screenshot received. Admin will verify and activate soon.")
    else:
        await update.message.reply_text("❗ No recent order found. Please select a hack and plan first.")

# ================ Admin Reply Handler ============
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        msg_id = update.message.reply_to_message.message_id
        if msg_id in user_queries:
            target = user_queries[msg_id]
            await context.bot.send_message(target, f"📬 Admin Reply:\n{update.message.text}")

# ================ Main ================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))
    app.run_polling()

if __name__ == "__main__":
    main()

