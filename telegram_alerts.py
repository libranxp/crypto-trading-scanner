import os
import requests
import logging

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

logger = logging.getLogger(__name__)

def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logger.warning("Telegram credentials not set; skipping alert.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        logger.exception("Failed to send Telegram message")
        return False

def send_telegram_alert_for_coin(coin: dict):
    # coin is validated upstream so we can format safely
    name = coin.get("name", "Unknown")
    symbol = coin.get("symbol", "UNK")
    price = coin.get("price", 0)
    volume = coin.get("volume", 0)
    rsi = coin.get("rsi", "N/A")
    rvol = coin.get("rvol", "N/A")
    sentiment = coin.get("sentiment_score", "N/A")
    ai_score = coin.get("ai_score", "N/A")
    vwap_prox = coin.get("vwap_proximity", 0)

    msg = (
        f"🚨 *Crypto Alert*\n"
        f"🪙 *{name}* ({symbol})\n"
        f"💰 Price: `${price:.6f}`\n"
        f"📊 Volume(24h): `${volume:,}`\n"
        f"📈 RSI: {rsi}\n"
        f"📉 RVOL: {rvol}\n"
        f"📍 VWAP proximity: {vwap_prox*100:.2f}%\n"
        f"⭐ Sentiment: {sentiment}\n"
        f"🤖 AI score: {ai_score}\n"
        f"\n{coin.get('coingecko_url','')}"
    )
    return send_telegram_message(msg)
