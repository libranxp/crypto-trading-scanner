import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

def send_telegram_alert(alert):
    msg = (
        f"🚨 *Crypto Alert*\n"
        f"🪙 Symbol: {alert['symbol'].upper()}\n"
        f"🤖 AI Score: {alert.get('ai_score', 0):.2f}\n"
        f"📊 Catalysts: {alert.get('catalysts', 'N/A')}\n"
        f"🐦 Twitter Mentions: {alert.get('twitter', {}).get('mentions',0)}\n"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": msg, "parse_mode":"Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram alert failed: {e}")
