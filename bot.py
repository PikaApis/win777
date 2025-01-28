import requests
import random
import time
from datetime import datetime, timedelta
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler
from telegram.error import TimedOut, BadRequest

# ✅ Telegram Bot Token and Channel ID
BOT_TOKEN = "7713244545:AAH1Qck0DVvLTrT1CTFGR1lwevfCBGfgM8M"
CHANNEL_ID = "@shaha_dat"

# ✅ Global Variables
prediction_state = False
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
        return None


# ✅ Function to send prediction messages with a timer
async def send_prediction_with_timer(bot, period, prediction):
    # ✅ Convert to Bangladesh Time (UTC+6)
    current_time = (datetime.utcnow() + timedelta(hours=6)).strftime('%H:%M:%S')
    invite_link = '<a href="https://wintk777.com/register?r_code=BTtzx94946">🔗 Invite Link</a>'
    
    try:
        msg = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"""
📢 <b>WinTk777 1 Minute 🎰</b>
🕒 <b>Time:</b> {current_time}
🔢 <b>Period:</b> <code>{period}</code>
🎲 <b>Bet:</b> <code>{prediction}</code>
⏳ <b>Ends in:</b> 00:60 seconds
{invite_link}
            """.strip(),
            parse_mode=ParseMode.HTML
        )

        # ✅ Update the message every 3 seconds
        for remaining in range(57, -1, -3):
            current_time = (datetime.utcnow() + timedelta(hours=6)).strftime('%H:%M:%S')
            await msg.edit_text(
                text=f"""
📢 <b>WinTk777 1 Minute 🎰</b>
🕒 <b>Time:</b> {current_time}
🔢 <b>Period:</b> <code>{period}</code>
🎲 <b>Bet:</b> <code>{prediction}</code>
⏳ <b>Ends in:</b> 00:{remaining:02d} seconds
{invite_link}
                """.strip(),
                parse_mode=ParseMode.HTML
            )
            time.sleep(3)

        return msg
    except (TimedOut, BadRequest) as e:
        print(f"❌ Error updating message: {e}")


# ✅ Function to generate predictions and evaluate outcomes
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
        msg = await send_prediction_with_timer(bot, ongoing_period, prediction)
        
        results = get_results()
        if not results:
            continue

        games_list = results.get("data", {}).get("gameslist", [])
        for game in games_list:
            if game["period"] == ongoing_period:
                amount = game["amount"]
                result = "Big" if amount >= 5 else "Small"
                outcome = "✅ Win" if result == prediction else "❌ Lose"

                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"""
🎯 <b>Prediction Result</b> 🎰
🔢 <b>Period:</b> <code>{ongoing_period}</code>
🎲 <b>Prediction:</b> <code>{prediction}</code>
🏆 <b>Result:</b> <code>{result}</code>
📊 <b>Outcome:</b> {outcome}
                    """.strip(),
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=msg.message_id
                )

                gif_url = WIN_GIF if outcome == "✅ Win" else LOSE_GIF
                await bot.send_animation(chat_id=CHANNEL_ID, animation=gif_url)
                break


# ✅ Start and Stop Commands
async def start(update, context):
    await update.message.reply_text("✅ Use /startpredictions to begin & /offpredictions to stop.")


async def start_predictions(update, context):
    global prediction_state
    prediction_state = True
    bot = context.bot
    await generate_predictions(bot)


async def stop_predictions(update, context):
    global prediction_state
    prediction_state = False
    await update.message.reply_text("🛑 Predictions stopped!")


# ✅ Main Function
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("startpredictions", start_predictions))
    application.add_handler(CommandHandler("offpredictions", stop_predictions))
    application.run_polling()


if __name__ == "__main__":
    main()
