import os
import time
import requests
from fastapi import FastAPI
from typing import List, Dict

app = FastAPI()

# --- Environment Variables ---
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CRYPTODESK_API_KEY = os.getenv("CRYPTODESK_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
TAPPI_API_KEY = os.getenv("TAPPI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

ALERT_HISTORY = {}  # symbol: last_alert_timestamp

# --- API Integrations (stubs, expand as needed) ---

def fetch_coingecko_coins() -> List[Dict]:
    coins = []
    page = 1
    while True:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": True
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        if not data:
            break
        coins.extend(data)
        page += 1
        if page > 4:  # Limit to 1000 coins for performance
            break
    return coins

def fetch_coinmarketcap_data(symbol: str) -> Dict:
    if not COINMARKETCAP_API_KEY:
        return {}
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"symbol": symbol}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        return {}
    data = resp.json().get("data", {}).get(symbol, {})
    return data

def fetch_lunarcrush_social(symbol: str) -> Dict:
    if not LUNARCRUSH_API_KEY:
        return {}
    url = f"https://api.lunarcrush.com/v2?data=assets&key={LUNARCRUSH_API_KEY}&symbol={symbol}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return {}
    data = resp.json().get("data", [{}])[0]
    return {
        "twitter_mentions": data.get("twitter_mentions", 0),
        "engagement_score": data.get("galaxy_score", 0),
        "influencer_flag": data.get("influencer_score", 0) > 0,
        "sentiment_score": data.get("alt_rank", 0) / 100 if data.get("alt_rank") else 0
    }

def fetch_cryptopanic_news():
    if not CRYPTOPANIC_API_KEY:
        return []
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=trending"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    return [{"title": post["title"], "url": post["url"]} for post in data.get("results", [])]

def fetch_messari_metrics(symbol: str) -> Dict:
    if not MESSARI_API_KEY:
        return {}
    url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
    headers = {"x-messari-api-key": MESSARI_API_KEY}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {}
    return resp.json().get("data", {}).get("market_data", {})

def fetch_alphavantage_technicals(symbol: str) -> Dict:
    if not ALPHAVANTAGE_API_KEY:
        return {}
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "RSI",
        "symbol": symbol,
        "interval": "daily",
        "time_period": 14,
        "series_type": "close",
        "apikey": ALPHAVANTAGE_API_KEY
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return {}
    data = resp.json()
    rsi = None
    try:
        rsi = float(list(data["Technical Analysis: RSI"].values())[0]["RSI"])
    except Exception:
        rsi = None
    return {"rsi": rsi}

# Add similar stubs for other APIs as needed (Polygon, Reddit, Santiment, Tappi, NewsAPI, etc.)

# --- Indicator Calculations ---

def calculate_indicators(coin: Dict, symbol: str) -> Dict:
    # Use sparkline for EMA/VWAP/RVOL, AlphaVantage for RSI
    prices = coin.get("sparkline_in_7d", {}).get("price", [])
    if len(prices) < 50:
        return {}
    # EMA calculation (5, 13, 50)
    def ema(prices, period):
        k = 2 / (period + 1)
        ema_val = prices[0]
        for price in prices[1:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val
    ema5 = ema(prices[-20:], 5)
    ema13 = ema(prices[-50:], 13)
    ema50 = ema(prices, 50)
    ema_alignment = ema5 > ema13 > ema50

    # VWAP proximity (approximate)
    vwap = sum(prices[-20:]) / len(prices[-20:])
    vwap_proximity = abs(coin["current_price"] - vwap) / vwap <= 0.02

    # RVOL (relative volume, 24h vs 7d avg)
    avg_vol = coin.get("total_volume", 0) / 7
  
