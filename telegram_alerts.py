import os
import requests

BOT = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")

def _fmt_price(x):
    if x is None: return "—"
    return f"${x:,.6f}" if x < 1 else f"${x:,.2f}"

def send_telegram_alert(payload: dict):
    """Format per your spec and send."""
    if not (BOT and CHAT_ID):
        return  # silently skip if Telegram not configured

    tkr = payload["symbol"]
    price = _fmt_price(payload.get("price"))
    chg = payload.get("change_pct", 0.0)
    ai_score = payload.get("ai_score", 0.0)
    reason = payload.get("ai_reason", "")
    sl = _fmt_price(payload.get("risk", {}).get("stop_loss"))
    tp = _fmt_price(payload.get("risk", {}).get("take_profit"))
    pos = payload.get("risk", {}).get("position_size", "—")

    sents = payload.get("sentiment", {})
    sent_label = "Bullish" if sents.get("score", 0) >= 0.6 else ("Bearish" if sents.get("score", 0) <= 0.4 else "Neutral")

    links = payload.get("links", {})
    tv = links.get("tradingview", "")
    news = (links.get("news") or [""])[0]
    catalyst = (links.get("catalyst") or links.get("news") or [""])[0]
    reddit = (links.get("reddit") or [""])[0]
    tweet = (links.get("tweet") or [""])[0]

    text = (
f"TELEGRAM ALERTS\n"
f"🚨 New Signal: ${tkr}\n\n"
f"📈 Price: {price} | Change: {chg:+.2f}%\n"
f"📊 AI Score: {ai_score:.1f}/10 (High Confidence)\n"
f"🧠 Reason: \"{reason}\"\n"
f"📍 Risk: SL = {sl} | TP = {tp} | Position Size: {pos}\n"
f"📡 Sentiment: {sent_label} (Twitter + Reddit + News)\n"
f"📰 Catalyst: {catalyst or '—'}\n\n"
f"🔗 [TradingView Chart]({tv})\n"
f"🔗 [News Source]({news})\n"
f"🔗 [Reddit Thread]({reddit or news})\n"
f"🔗 [Tweet]({tweet or news})\n"
    )

    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    resp = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=20)
    if not resp.ok:
        # Best effort; don't crash the pipeline for Telegram issues
        pass
