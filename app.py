import os
import time
import logging
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache settings
CACHE = {"data": None, "timestamp": 0}
CACHE_TTL = 60  # cache results for 60 seconds

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "volume_desc",
    "per_page": 250,
    "page": 1,
    "sparkline": False,
}


def fetch_from_coingecko():
    """Fetch coins from CoinGecko with retry + caching."""
    global CACHE

    now = time.time()
    # If cache is fresh, return it
    if CACHE["data"] and (now - CACHE["timestamp"] < CACHE_TTL):
        logger.info("Using cached CoinGecko data")
        return CACHE["data"]

    tries = 3
    for attempt in range(tries):
        try:
            resp = requests.get(COINGECKO_URL, params=PARAMS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                CACHE = {"data": data, "timestamp": now}
                logger.info(f"Fetched {len(data)} coins from CoinGecko")
                return data
            elif resp.status_code == 429:
                # Rate limited
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limited by CoinGecko, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"CoinGecko error {resp.status_code}: {resp.text}")
                break
        except Exception as e:
            logger.error(f"Error fetching CoinGecko: {e}")
            time.sleep(2)

    # fallback to cache if fetch fails
    if CACHE["data"]:
        logger.warning("Using cached CoinGecko data (fallback)")
        return CACHE["data"]

    return []


@app.route("/")
def home():
    return jsonify({"status": "running"})


@app.route("/scan")
def scan():
    coins = fetch_from_coingecko()
    results = []

    for coin in coins:
        try:
            # Example filter: price between $0.01 and $10
            if 0.01 <= coin["current_price"] <= 10:
                results.append({
                    "symbol": coin["symbol"],
                    "name": coin["name"],
                    "price": coin["current_price"],
                    "volume": coin["total_volume"],
                    "market_cap": coin["market_cap"]
                })
        except Exception as e:
            logger.error(f"Error processing coin: {e}")

    logger.info(f"Coins passing all filters: {len(results)}")
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
