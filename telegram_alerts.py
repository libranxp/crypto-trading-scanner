# telegram_alerts.py
import httpx
from typing import Dict, Any
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from db import log_alert
import logging
logger = logging.getLogger(__name__)

TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def _fmt_money(v):
    try:
        if v is None: return "—"
        if v >= 1e9: return f"${v/1e9:.2f}B"
        if v >= 1e6: return f"${v/1e6:.2f}M"
        if v >= 1e3: return f"${v/1e3:.2f}K"
        return f"${v:.2f}"
    except:
        return str(v)

def build_message(d: Dict[str, Any]) -> str:
    # Required fields are guarded with defaults
    t = d.get("symbol", "TICKER")
    price = d.get("price", 0.0)
    chg = d.get("pct_change_24h", 0.0)
    ai = d.get("ai_score", 0.0)
    reason = d.get("ai_narrative", "Signal detected")
    risk = d.get("risk", {})
    sl = risk.get("stop_loss")
    tp = risk.get("take_profit")
    pos = risk.get("position_size")
    sent_label = d.get("sentiment", {}).get("label", "Neutral")
    sent_links = d.get("sentiment_links", [])
    best_catalyst = d.get("catalyst", {})
    tv_link = d.get("tradingview_url", f"https://www.tradingview.com/symbols/{t}/")

    news_link = best_catalyst.get("url") or d.get("news_url") or "https://news.google.com/"
    reddit_link = d.get("reddit_url") or "https://reddit.com/r/cryptocurrency"
    tweet_link = d.get("tweet_url") or "https://twitter.com/"

    lines = [
        "TELEGRAM ALERTS",
        f"🚨 New Signal: ${t}",
        "",
        f"📈 Price: ${price:.6f} | Change: {chg:+.2f}%",
        f"📊 AI Score: {ai:.1f}/10 (High Confidence)" if ai >= 7 else f"📊 AI Score: {ai:.1f}/10",
        f"🧠 Reason: \"{reason}\"",
        f"📍 Risk: SL = ${sl:.6f} | TP = ${tp:.6f} | Position Size: {_fmt_money(pos)}",
        f"📡 Sentiment: {sent_label} (Twitter + Reddit + News)",
        f"📰 Catalyst: {best_catalyst.get('source','News')} + {best_catalyst.get('title','Update')}",
        "",
        f"🔗 <a href=\"{tv_link}\">TradingView Chart</a>",
        f"🔗 <a href=\"{news_link}\">News Source</a>",
        f"🔗 <a href=\"{reddit_link}\">Reddit Thread</a>",
        f"🔗 <a href=\"{tweet_link}\">Tweet</a>",
        "",
        d.get("time_str", "")
    ]
    return "\n".join(lines)

def send_alert(payload: Dict[str, Any]) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logger.warning("Telegram env missing; skipping alert.")
        return
    msg = build_message(payload)
    try:
        r = httpx.post(TG_API, timeout=10, data={
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        })
        r.raise_for_status()
        log_alert(payload.get("symbol","TICKER"), payload)
    except Exception as e:
        logger.exception("Telegram send failed: %s", e)
