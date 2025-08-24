import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

def send_telegram_alert(coin: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        return
    message = (
        f"🚨 *Crypto Alert*\n"
        f"🪙 {coin['name']} ({coin['symbol']})\n"
        f"💰 Price: ${coin['price']:.4f}\n"
        f"📊 MC: ${coin['market_cap']:,} | Vol(24h): ${coin['volume']:,}\n"
        f"📈 RSI: {coin.get('rsi','N/A'):.2f} | RVOL: {coin.get('rvol','N/A'):.2f}\n"
        f"🧭 EMA align: {'Yes' if coin.get('ema_aligned') else 'No'} | VWAP Δ: {coin.get('vwap_proximity',0)*100:.2f}%\n"
        f"💬 Mentions: {coin.get('mentions',0)} | 📣 Engagement: {coin.get('engagement',0)} | ⭐ Sent: {coin.get('sentiment_score',0):.2f}\n"
        f"📅 Events: {coin.get('events',0)} | 🤖 AI Score: {coin.get('ai_score','N/A')} | ⚠️ Risk: {coin.get('risk','N/A')}\n"
        f"🔗 {coin.get('coingecko_url','')}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15).raise_for_status()
    except Exception:
        pass
