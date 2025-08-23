import os
import time
import requests
from fastapi import FastAPI
from typing import List, Dict
from functools import lru_cache

app = FastAPI()

LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

ALERT_HISTORY = {}
CACHE_EXPIRY = 600  # 10 minutes cache for CoinGecko data
_cached_coins = None
_cache_time = 0

def retry_get(url, params=None, headers=None, max_retries=3, backoff=2):
    for i in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:
                wait = backoff ** i
                print(f"Rate limited by {url}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"Request error {url}: {e}")
            if i == max_retries - 1:
                return None
            time.sleep(backoff ** i)
    return None

def fetch_coingecko_coins_cached() -> List[Dict]:
    global _cached_coins, _cache_time
    now = time.time()
    if _cached_coins and now - _cache_time < CACHE_EXPIRY:
        print(f"Using cached CoinGecko data: {len(_cached_coins)} coins")
        return _cached_coins

    coins = []
    pages_to_fetch = 1  # reduce pages to avoid rate limits
    for page in range(1, pages_to_fetch + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": page,
            "sparkline": True
        }
        resp = retry_get(url, params=params)
        if resp is None:
            break
        data = resp.json()
        if not data:
            break
        coins.extend(data)
    _cached_coins = coins
    _cache_time = now
    print(f"Fetched {len(coins)} coins from CoinGecko (cached).")
    return coins

def calculate_indicators(coin: Dict) -> Dict:
    prices = coin.get("sparkline_in_7d", {}).get("price", [])
    if not prices or len(prices) < 20:
        # Relaxed minimum sparkline length to 20
        print(f"{coin['symbol'].upper()} skipped: insufficient sparkline data ({len(prices) if prices else 0})")
        return {}

    # Calculate RSI with fallback for shorter data
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    window = min(14, len(deltas))
    gains = [d for d in deltas[-window:] if d > 0]
    losses = [-d for d in deltas[-window:] if d < 0]
    avg_gain = sum(gains)/window if gains else 0.0001
    avg_loss = sum(losses)/window if losses else 0.0001
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    def ema(prices_list, period):
        k = 2 / (period + 1)
        ema_val = prices_list[0]
        for price in prices_list[1:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val

    ema5 = ema(prices[-20:], 5) if len(prices) >= 20 else ema(prices, 5)
    ema13 = ema(prices[-50:], 13) if len(prices) >= 50 else ema(prices, min(13, len(prices)))
    ema50 = ema(prices, 50) if len(prices) >= 50 else ema(prices, len(prices))

    ema_alignment = ema5 > ema13 > ema50

    vwap = sum(prices[-20:]) / len(prices[-20:]) if len(prices) >= 20 else sum(prices) / len(prices)
    vwap_proximity = abs(coin["current_price"] - vwap) / vwap <= 0.02

    avg_vol = coin.get("total_volume", 0) / 7 if coin.get("total_volume") else 0.0001
    rvol = coin.get("total_volume", 0) / avg_vol if avg_vol else 0

    if len(prices) > 12:
        last_hour = prices[-12:]
        pump_filter = (max(last_hour) - min(last_hour)) / min(last_hour) > 0.5 and coin.get("total_volume", 0) < 20_000_000
    else:
        pump_filter = False

    return {
        "rsi": rsi,
        "ema_alignment": ema_alignment,
        "vwap_proximity": vwap_proximity,
        "rvol": rvol,
        "pump_filter": pump_filter
    }

def passes_filters(coin: Dict, indicators: Dict, social: Dict, sentiment: float, news_mentions: int, twitter_mentions: int, reddit_mentions: int) -> bool:
    price = coin["current_price"]
    volume = coin["total_volume"]
    market_cap = coin.get("market_cap", 0)
    price_change = coin.get("price_change_percentage_24h", 0)
    symbol = coin["symbol"].upper()
    name = coin["name"].lower()

    # Loosened filters for testing - adjust as needed
    if not (0.001 <= price <= 100):
        print(f"{symbol} failed price filter")
        return False
    if volume < 1_000_000:
        print(f"{symbol} failed volume filter")
        return False
    if not (-10 <= price_change <= 50):
        print(f"{symbol} failed price change filter")
        return False
    if not (5_000_000 <= market_cap <= 5_000_000_000):
        print(f"{symbol} failed market cap filter")
        return False
    if not (30 <= indicators.get("rsi", 0) <= 80):
        print(f"{symbol} failed RSI filter")
        return False
    if indicators.get("rvol", 0) < 1.5:
        print(f"{symbol} failed RVOL filter")
        return False
    if not indicators.get("ema_alignment", False):
        print(f"{symbol} failed EMA alignment filter")
        return False
    if not indicators.get("vwap_proximity", False):
        print(f"{symbol} failed VWAP proximity filter")
        return False
    if indicators.get("pump_filter", False):
        print(f"{symbol} failed pump filter")
        return False
    if ALERT_HISTORY.get(symbol, 0) > time.time() - 6*3600:
        print(f"{symbol} failed duplicate alert filter")
        return False
    if (social.get("twitter_mentions", 0) + twitter_mentions < 5 or
        social.get("engagement_score", 0) < 50 or
        sentiment < 0.5):
        print(f"{symbol} failed social/sentiment filter")
        return False
    if "meme" in name or "doge" in name or "shiba" in name or "inu" in name:
        if not (volume > 1_000_000 and sentiment >= 0.5):
            print(f"{symbol} failed meme coin filter")
            return False
    return True

def send_telegram_alert(coin: Dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not set.")
        return
    msg = (
        f"🚨 *{coin['name']}* ({coin['symbol'].upper()})\n"
        f"Price: ${coin['current_price']:.4f}\n"
        f"Volume: ${coin['total_volume']:,}\n"
        f"Market Cap: ${coin.get('market_cap', 0):,}\n"
        f"24h Change: {coin.get('price_change_percentage_24h', 0):.2f}%\n"
        f"https://www.coingecko.com/en/coins/{coin['id']}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=payload)
        print("Telegram alert sent:", r.text)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

@app.get("/")
def root():
    return {"message": "Crypto Trading Scanner API is running. Use /scan/auto for results."}

@app.head("/")
def root_head():
    return

@app.get("/scan/auto")
def scan_auto():
    coins = fetch_coingecko_coins_cached()
    print(f"Using cached CoinGecko data: {len(coins)} coins")
    results = []
    filtered = 0
    for coin in coins:
        symbol = coin["symbol"].upper()
        indicators = calculate_indicators(coin)
        if not indicators:
            continue
        social = fetch_lunarcrush_social(symbol)
        sentiment = fetch_santiment_sentiment(symbol)
        news_mentions = fetch_newsapi_mentions(symbol)
        twitter_mentions = fetch_twitter_mentions(symbol)
        reddit_mentions = fetch_reddit_mentions(symbol)
        if passes_filters(coin, indicators, social, sentiment, news_mentions, twitter_mentions, reddit_mentions):
            filtered += 1
            results.append({
                "symbol": symbol,
                "name": coin["name"],
                "price": coin["current_price"],
                "market_cap": coin.get("market_cap", 0),
                "volume": coin.get("total_volume", 0),
                "price_change_24h": coin.get("price_change_percentage_24h", 0),
                "rsi": indicators.get("rsi"),
                "rvol": indicators.get("rvol"),
                "ema_alignment": indicators.get("ema_alignment"),
                "vwap_proximity": indicators.get("vwap_proximity"),
                "twitter_mentions": social.get("twitter_mentions"),
                "engagement_score": social.get("engagement_score"),
                "influencer_flag": social.get("influencer_flag"),
                "sentiment_score": sentiment,
                "news_mentions": news_mentions,
                "reddit_mentions": reddit_mentions,
