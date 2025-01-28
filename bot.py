import requests
import random
import json
import time
import logging
from datetime import datetime, timedelta
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TimedOut, BadRequest

# ✅ Load Config (Admin, Channels, Bot State)
CONFIG_FILE = "dbw.json"
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"admin_id": None, "channels": [], "bot_running": False}

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

config = load_config()

# ✅ Telegram Bot Token
BOT_TOKEN = "7713244545:AAH1Qck0DVvLTrT1CTFGR1lwevfCBGfgM8M"
ADMIN_ID = config["admin_id"]

# ✅ Global Variables
prediction_state = config["bot_running"]
auth_token = ""
cookie_token = ""

# ✅ GIF/Video Links
WIN_GIF = "https://t.me/shaha_dat/265"
LOSE_GIF = "https://t.me/shaha_dat/264"

# ✅ Function to log in and retrieve tokens
def login():
    global auth_token, cookie_token
    login_url = "https://wintk777.com/api/webapi/login"
    login_payload = {"username": "1322401151", "pwd": "9vwRcqnJ9qNyME9"}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.post(login_url, data=login_payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        auth_token = data.get("value")
        cookie_token = data.get("token")
        print(f"✅ Login successful: Auth={auth_token}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {e}")
        notify_admin(f"⚠️ Login Error: {e}")

# ✅ Function to fetch game results
def get_results():
    global auth_token, cookie_token
    url = "https://wintk777.com/api/webapi/GetNoaverageEmerdList"
    headers = {"User-Agent": "Mozilla/5.0", "Cookie": f"token={cookie_token}; auth={auth_token}"}
    data = {"typeid": "1", "pageno": "0", "pageto": "10", "language": "vi"}

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching results: {e}")
        notify_admin(f"⚠️ Result Fetch Error: {e}")
        return None

# ✅ Notify Admin on Errors
def notify_admin(message):
    if ADMIN_ID:
        application.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode=ParseMode.HTML)

# ✅ Send Predictions
async def send_prediction(bot, period, prediction):
    current_time = (datetime.utcnow() + timedelta(hours=6)).strftime('%H:%M:%S')
    invite_link = '<a href="https://wintk777.com/register?r_code=BTtzx94946">🔗 Invite Link</a>'

    message_text = f"""
📢 <b>WinTk777 1 Minute 🎰</b>
🕒 <b>Time:</b> {current_time}
🔢 <b>Period:</b> <code>{period}</code>
🎲 <b>Bet:</b> <code>{prediction}</code>
⏳ <b>Ends in:</b> 00:60 seconds
{invite_link}
    """.strip()

    for channel in config["channels"]:
        await bot.send_message(chat_id=channel, text=message_text, parse_mode=ParseMode.HTML)

# ✅ Generate Predictions
async def generate_predictions(bot):
    global prediction_state
    while prediction_state:
        login()
        results = get_results()
        if not results or "period" not in results:
            time.sleep(60)
            continue

        ongoing_period = results.get("period")
        prediction = random.choice(["Big", "Small"])
        await send_prediction(bot, ongoing_period, prediction)

        results = get_results()
        if not results:
            continue

        games_list = results.get("data", {}).get("gameslist", [])
        for game in games_list:
            if game["period"] == ongoing_period:
                amount = game["amount"]
                result = "Big" if amount >= 5 else "Small"
                outcome = "✅ Win" if result == prediction else "❌ Lose"

                for channel in config["channels"]:
                    await bot.send_message(
                        chat_id=channel,
                        text=f"""
🎯 <b>Prediction Result</b> 🎰
🔢 <b>Period:</b> <code>{ongoing_period}</code>
🎲 <b>Prediction:</b> <code>{prediction}</code>
🏆 <b>Result:</b> <code>{result}</code>
📊 <b>Outcome:</b> {outcome}
                        """.strip(),
                        parse_mode=ParseMode.HTML
                    )
                    gif_url = WIN_GIF if outcome == "✅ Win" else LOSE_GIF
                    await bot.send_animation(chat_id=channel, animation=gif_url)
                break

# ✅ First-Time Admin Setup
async def set_admin(update, context):
    if update.message.text == "/pika99" and config["admin_id"] is None:
        config["admin_id"] = update.message.chat_id
        save_config(config)
        await update.message.reply_text("👑 You are now the admin!")

# ✅ Admin Commands
async def add_channel(update, context):
    if update.message.chat_id == ADMIN_ID:
        new_channel = context.args[0]
        config["channels"].append(new_channel)
        save_config(config)
        await update.message.reply_text(f"✅ Channel {new_channel} added!")

async def remove_channel(update, context):
    if update.message.chat_id == ADMIN_ID:
        channel = context.args[0]
        if channel in config["channels"]:
            config["channels"].remove(channel)
            save_config(config)
            await update.message.reply_text(f"❌ Channel {channel} removed!")

async def show_config(update, context):
    await update.message.reply_text(f"📋 Config: {json.dumps(config, indent=4)}")

# ✅ Main Function
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("pika99", set_admin))
    application.add_handler(CommandHandler("addchannel", add_channel))
    application.add_handler(CommandHandler("removechannel", remove_channel))
    application.add_handler(CommandHandler("showconfig", show_config))
    application.run_polling()

if __name__ == "__main__":
    main()
