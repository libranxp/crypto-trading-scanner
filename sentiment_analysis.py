import os
import requests
from config import LUNARCRUSH_API_KEY, SANTIMENT_API_KEY, COINMARKETCAL_API_KEY

def lunarcrush_sentiment(symbol: str) -> float:
    if not LUNARCRUSH_API_KEY:
        return 0.6
    try:
        url = f"https://lunarcrush.com/api3/assets?symbol={symbol.upper()}"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
        r = requests.get(url, headers=headers, timeout=20)
        data = r.json().get("data", [])
        if data:
            gs = data[0].get("galaxy_score")
            if gs is None: return 0.6
            # normalize 0–100 to 0–1
            return min(max(gs/100.0, 0), 1)
    except Exception:
        pass
    return 0.6

def santiment_mentions(symbol: str) -> int:
    if not SANTIMENT_API_KEY:
        return 15
    try:
        query = """
        { getMetric(metric:"social_volume_total"){
            timeseriesData(slug:"%s", from:"utc_now-1d", to:"utc_now", interval:"1d"){ value }
        } }""" % symbol.lower()
        url = "https://api.santiment.net/graphql"
        headers = {"Authorization": f"Apikey {SANTIMENT_API_KEY}"}
        r = requests.post(url, json={"query": query}, headers=headers, timeout=20)
        arr = r.json()["data"]["getMetric"]["timeseriesData"]
        return int(arr[0]["value"]) if arr else 0
    except Exception:
        return 15

def coinmarketcal_events(symbol: str) -> int:
    if not COINMARKETCAL_API_KEY:
        return 0
    try:
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        url = f"https://developers.coinmarketcal.com/v1/events?coins={symbol.lower()}"
        r = requests.get(url, headers=headers, timeout=20)
        return len(r.json().get("body", []))
    except Exception:
        return 0
