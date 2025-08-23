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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

ALERT_HISTORY = {}

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
                raise
            time.sleep(backoff ** i)
    return None

@lru_cache(maxsize=1)
def fetch_coingecko_coins_cached() -> List[Dict]:
    coins = []
    pages_to_fetch = 2  # reduce pages to limit calls
    for page in range(1, pages_to_fetch + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": True
        }
        try:
            resp = retry_get(url, params=params)
            if resp is None:
                break
            data = resp.json()
            if not data:
                break
            coins.extend(data)
        except Exception as e:
            print(f"Failed to fetch CoinGecko page {page}: {e}")
            break
    print(f"Fetched {len(coins)} coins from CoinGecko (cached).")
    return coins

# (Keep your other API fetch functions unchanged, or add caching similarly)

# Your calculate_indicators, passes_filters, send_telegram_alert, and scan_auto functions remain mostly unchanged,
# but call fetch_coingecko_coins_cached() instead of fetch_coingecko_coins()

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
            print(f"{symbol} skipped: insufficient sparkline data")
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
                "coingecko_url": f"https://www.coingecko.com/en/coins/{coin['id']}"
            })
            if ALERT_HISTORY.get(symbol, 0) < time.time() - 6*3600:
                send_telegram_alert(coin)
                ALERT_HISTORY[symbol] = time.time()
    print(f"Coins passing all filters: {filtered}")
    return {"results": results}
