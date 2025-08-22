from fastapi import FastAPI
import requests
import time
import os

app = FastAPI()

# Caching setup
COINGECKO_CACHE = {"data": None, "timestamp": 0}
CACHE_DURATION = 45 * 60  # 45 minutes in seconds

# CoinMarketCap API key from environment variable
CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

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
    # Normalize to CoinGecko-like format for downstream code
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

@app.get("/scan/auto")
def scan_auto():
    try:
        # Try CoinGecko first
        try:
            coins = fetch_coingecko_data()
            results = [
                {
                    "symbol": c["symbol"].upper(),
                    "name": c["name"],
                    "price": c["current_price"],
                    "market_cap": c["market_cap"],
                    "volume": c["total_volume"]
                }
                for c in coins
            ]
            return {"tier": 1, "results": results}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("CoinGecko rate limit hit. Falling back to CoinMarketCap.")
                # Try CoinMarketCap as backup
                if CMC_API_KEY:
                    results = fetch_coinmarketcap_data()
                    return {"tier": 1, "results": results, "source": "coinmarketcap"}
                else:
                    print("CoinMarketCap API key not set.")
                    return {"tier": 1, "results": [], "error": "CoinGecko rate limit hit and no CoinMarketCap API key set"}
            else:
                raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"tier": 1, "results": [], "error": str(e)}
