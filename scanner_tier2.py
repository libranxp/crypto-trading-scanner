import os
import requests
import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from telegram_alerts import send_telegram_alert

# Environment variables
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

def get_lunarcrush_sentiment(symbol):
    try:
        url = f"https://lunarcrush.com/api3/assets?symbol={symbol.upper()}"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json().get("data", [])
        if data:
            return data[0].get("galaxy_score", 50)
    except Exception:
        return 50

def get_santiment_sentiment(symbol):
    try:
        query = """
        {
          getMetric(metric: "social_volume_total") {
            timeseriesData(
              slug: "%s"
              from: "utc_now-1d"
              to: "utc_now"
              interval: "1d"
            ) {
              value
            }
          }
        }
        """ % symbol.lower()
        url = "https://api.santiment.net/graphql"
        headers = {"Authorization": f"Apikey {SANTIMENT_API_KEY}"}
        resp = requests.post(url, json={"query": query}, headers=headers, timeout=30)
        return resp.json()["data"]["getMetric"]["timeseriesData"][0]["value"]
    except Exception:
        return 0

def get_coinmarketcal_events(symbol):
    try:
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        url = f"https://developers.coinmarketcal.com/v1/events?coins={symbol.lower()}"
        resp = requests.get(url, headers=headers, timeout=30)
        events = resp.json().get("body", [])
        return len(events)
    except Exception:
        return 0

def calculate_ai_score(coin):
    """Compute AI Score based on filters"""
    score = 0
    if 50 <= coin.get("rsi", 0) <= 70: score += 1
    if coin.get("rvol", 0) > 2: score += 1
    if coin.get("sentiment_score", 0) > 0.6: score += 1
    if coin.get("twitter_mentions", 0) >= 10: score += 1
    if coin.get("engagement_score", 0) >= 100: score += 1
    return score

def tier2_scan():
    logging.info("🔍 Running Tier 2 Deep Scan...")
    results = supabase.table("tier1_results").select("*").order("timestamp", desc=True).limit(20).execute()
    candidates = results.data or []

    alerts = []
    for coin in candidates:
        # Check duplicate alerts
        recent_alerts = supabase.table("alerts").select("*").eq("symbol", coin["symbol"]).order("timestamp", desc=True).limit(1).execute()
        if recent_alerts.data:
            last_time = datetime.fromisoformat(recent_alerts.data[0]["timestamp"])
            if datetime.now(timezone.utc) - last_time < timedelta(hours=6):
                continue

        # Sentiment + Catalyst
        sentiment_score = get_lunarcrush_sentiment(coin["symbol"])
        social_volume = get_santiment_sentiment(coin["symbol"])
        events = get_coinmarketcal_events(coin["symbol"])

        enriched = {
            **coin,
            "sentiment_score": sentiment_score,
            "twitter_mentions": social_volume,
            "engagement_score": social_volume * 10,
            "events": events,
            "ai_score": calculate_ai_score(coin),
            "risk": "Medium" if sentiment_score > 60 else "High",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Send Telegram Alert
        send_telegram_alert(enriched)

        # Save to Supabase
        supabase.table("alerts").insert(enriched).execute()
        alerts.append(enriched)

    logging.info(f"✅ {len(alerts)} Tier 2 alerts sent.")
    return alerts

if __name__ == "__main__":
    tier2_scan()
