from fastapi import FastAPI, Query
import requests
import time
import os

app = FastAPI()

# Cache for CoinGecko data
COINGECKO_CACHE = {"data": None, "timestamp": 0}
CACHE_DURATION = 45 * 60  # 45 minutes

# Environment variables for API keys
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Use your TELEGRAM_CHANNEL_ID here

def fetch_coingecko_data():
    now = time.time()
    if COINGECKO_CACHE["data"] and now - COINGECKO_CACHE["timestamp"] < CACHE_DURATION:
        print("Using cached CoinGecko data")
        return COINGECKO_CACHE["data"]
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    COINGECKO_CACHE["data"] = data
    COINGECKO_CACHE["timestamp"] = now
    print("Fetched new CoinGecko data")
    return data

def fetch_coinmarketcap_data():
    if not CMC_API_KEY:
        print("CoinMarketCap API key not set.")
        return []
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }
    params = {
        "start": "1",
        "limit": "100",
        "convert": "USD"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    results = []
    for coin in data["data"]:
        results.append({
            "symbol": coin["symbol"],
            "name": coin["name"],
            "price": coin["quote"]["USD"]["price"],
            "market_cap": coin["quote"]["USD"]["market_cap"],
            "volume": coin["quote"]["USD"]["volume_24h"]
        })
    print("Fetched new CoinMarketCap data")
    return results

def fetch_lunarcrush_sentiment(symbol):
    if not LUNARCRUSH_API_KEY:
        print("LunarCrush API key not set.")
        return None
    url = f"https://api.lunarcrush.com/v2?data=assets&key={LUNARCRUSH_API_KEY}&symbol={symbol}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    sentiment = data.get("data", [{}])[0].get("galaxy_score", None)
    print(f"Fetched LunarCrush sentiment for {symbol}: {sentiment}")
    return sentiment

def fetch_messari_data(symbol):
    if not MESSARI_API_KEY:
        print("Messari API key not set.")
        return None
    url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
    headers = {"x-messari-api-key": MESSARI_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Messari data fetch failed for {symbol}")
        return None
    data = response.json()
    return data.get("data", {}).get("market_data", {})

def fetch_cryptopanic_news():
    if not CRYPTOPANIC_API_KEY:
        print("CryptoPanic API key not set.")
        return []
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=trending"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    news = [{"title": post["title"], "url": post["url"]} for post in data.get("results", [])]
    print(f"Fetched {len(news)} news articles from CryptoPanic")
    return news

def fetch_alphavantage_data(symbol):
    if not ALPHAVANTAGE_API_KEY:
        print("AlphaVantage API key not set.")
        return None
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": ALPHAVANTAGE_API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"Fetched AlphaVantage data for {symbol}")
    return data

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or channel ID not set.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        print(f"Telegram alert sent: {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

@app.get("/scan/auto")
def scan_auto():
    try:
        coins = fetch_coingecko_data()
        results = []
        for c in coins:
            symbol = c["symbol"].upper()
            sentiment = fetch_lunarcrush_sentiment(symbol)
            messari_data = fetch_messari_data(symbol)
            results.append({
                "symbol": symbol,
                "name": c["name"],
                "price": c["current_price"],
                "market_cap": c["market_cap"],
                "volume": c["total_volume"],
                "lunarcrush_sentiment": sentiment,
                "messari_market_data": messari_data
            })
        news = fetch_cryptopanic_news()
        return {"tier": 1, "results": results, "news": news, "source": "coingecko + others"}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"tier": 1, "results": [], "error": str(e)}

@app.get("/scan/manual")
def scan_manual(symbols: str = Query(..., description="Comma-separated list of symbols")):
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        coins = fetch_coingecko_data()
        found = []
        for c in coins:
            symbol = c["symbol"].upper()
            if symbol in symbol_list and c["current_price"] > 10000:
                messari_data = fetch_messari_data(symbol)
                sentiment = fetch_lunarcrush_sentiment(symbol)
                found.append({
                    "symbol": symbol,
                    "name": c["name"],
                    "price": c["current_price"],
                    "market_cap": c["market_cap"],
                    "volume": c["total_volume"],
                    "lunarcrush_sentiment": sentiment,
                    "messari_market_data": messari_data
                })
                send_telegram_alert(
                    f"ALERT: {c['name']} ({symbol}) price is ${c['current_price']:,}"
                )
        return {"tier": 2, "results": found}
    except Exception as e:
        print(f"Error in manual scan: {e}")
        return {"tier": 2, "results": [], "error": str(e)}
