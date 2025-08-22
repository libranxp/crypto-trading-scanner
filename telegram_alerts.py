import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

def send_telegram_alert(coin):
    message = (
        f"🚨 *Crypto Alert*\n"
        f"🪙 Name: {coin['name']} ({coin['symbol'].upper()})\n"
        f"💰 Price: ${coin['price']:.4f}\n"
        f"📊 Volume (24h): ${coin['volume']:,}\n"
        f"📈 RSI: {coin.get('rsi', 'N/A')}\n"
        f"📉 RVOL: {coin.get('rvol', 'N/A')}\n"
        f"📊 EMA Alignment: {'Yes' if coin.get('ema_aligned', False) else 'No'}\n"
        f"📍 VWAP Proximity: {coin.get('vwap_proximity', 0)*100:.2f}%\n"
        f"🐦 Twitter Mentions: {coin.get('twitter_mentions', 0)}\n"
        f"🔥 Engagement Score: {coin.get('engagement_score', 0)}\n"
        f"⭐ Sentiment Score: {coin.get('sentiment_score', 0):.2f}\n"
        f"🤖 AI Score: {coin.get('ai_score', 'N/A')}\n"
        f"⚠️ Risk: {coin.get('risk', 'N/A')}\n"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram alert failed: {e}")
