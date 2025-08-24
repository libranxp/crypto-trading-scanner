import json
from datetime import datetime, timedelta, timezone
from config import (
    ALERTS_LOG_FILE, TIER1_CACHE_FILE, TIER2_CACHE_FILE
)
from sentiment_analysis import lunarcrush_sentiment, santiment_mentions, coinmarketcal_events
from telegram_alerts import send_telegram_alert

def _load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text() or "{}")
    except Exception:
        return {}

def _save_json(path, obj):
    path.write_text(json.dumps(obj, indent=2))

def _duplicate_recent(symbol: str, hours: int = 6) -> bool:
    log = _load_json(ALERTS_LOG_FILE)
    last = log.get(symbol)
    if not last:
        return False
    last_dt = datetime.fromisoformat(last)
    return (datetime.now(timezone.utc) - last_dt) < timedelta(hours=hours)

def _mark_alert(symbol: str):
    log = _load_json(ALERTS_LOG_FILE)
    log[symbol] = datetime.now(timezone.utc).isoformat()
    _save_json(ALERTS_LOG_FILE, log)

def ai_score(item):
    score = 0
    if 50 <= item.get("rsi", 0) <= 70: score += 1
    if item.get("rvol", 0) >= 2:       score += 1
    if item.get("sentiment_score", 0) >= 0.6: score += 1
    if item.get("mentions", 0) >= 10:  score += 1
    if item.get("engagement", 0) >= 100: score += 1
    if item.get("events", 0) > 0:      score += 1
    return score

def run_tier2():
    t1 = _load_json(TIER1_CACHE_FILE)
    base = t1.get("results", [])

    enriched = []
    for coin in base:
        sym = coin["symbol"]

        if _duplicate_recent(sym):
            continue

        sent = lunarcrush_sentiment(sym)
        mentions = santiment_mentions(sym)
        events = coinmarketcal_events(sym)
        eng = mentions * 10  # rough proxy

        item = {
            **coin,
            "sentiment_score": sent,
            "mentions": mentions,
            "engagement": eng,
            "events": events,
        }
        item["ai_score"] = ai_score(item)
        item["risk"] = "Medium" if item["sentiment_score"] >= 0.6 and item["rvol"] >= 2 else "High"

        # Alert + mark
        send_telegram_alert(item)
        _mark_alert(sym)

        enriched.append(item)

    _save_json(TIER2_CACHE_FILE, {"results": enriched, "timestamp": datetime.now(timezone.utc).isoformat()})
    return enriched
