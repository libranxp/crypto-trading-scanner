import os
import time
import logging
from typing import List, Dict, Any, Optional

import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------- App & logging ----------
app = FastAPI(title="Crypto Scanner", version="1.1.0")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crypto-scanner")

# Allow all origins by default (tighten if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Cache ----------
CACHE: Dict[str, Any] = {"data": None, "timestamp": 0.0}
CACHE_TTL = float(os.environ.get("CACHE_TTL", "60"))  # seconds

# ---------- CoinGecko ----------
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "volume_desc",
    "per_page": 250,
    "page": 1,
    "sparkline": "false",
}

def fetch_from_coingecko() -> List[Dict[str, Any]]:
    """
    Fetch coins from CoinGecko with simple retry + in-memory caching.
    Using sync requests is fine in FastAPI: it runs in a threadpool.
    """
    now = time.time()

    # Serve fresh cache
    if CACHE["data"] is not None and (now - CACHE["timestamp"] < CACHE_TTL):
        logger.info("Using cached CoinGecko data")
        return CACHE["data"]

    tries = 3
    last_err: Optional[str] = None

    for attempt in range(1, tries + 1):
        try:
            resp = requests.get(COINGECKO_URL, params=PARAMS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                CACHE["data"] = data
                CACHE["timestamp"] = now
                logger.info("Fetched %d coins from CoinGecko", len(data))
                return data

            if resp.status_code == 429:
                wait_time = attempt * 2
                logger.warning("Rate-limited by CoinGecko (429). Retry in %ss...", wait_time)
                time.sleep(wait_time)
                continue

            # Other HTTP errors
            last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            logger.error("CoinGecko error: %s", last_err)
            break

        except Exception as e:  # network/timeouts etc.
            last_err = str(e)
            logger.error("Error fetching CoinGecko: %s", last_err)
            time.sleep(2)

    # Fallback to stale cache if available
    if CACHE["data"] is not None:
        logger.warning("Using stale cached CoinGecko data (fallback). Last error: %s", last_err)
        return CACHE["data"]

    logger.error("Failed to fetch and no cache available. Last error: %s", last_err)
    return []


# ---------- Routes ----------
@app.get("/")
def root():
    return {"status": "ok", "service": "crypto-scanner", "version": app.version}

@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

@app.get("/scan")
def scan(
    min_price: float = Query(0.01, ge=0.0, description="Minimum price in USD"),
    max_price: float = Query(10.0, gt=0.0, description="Maximum price in USD"),
):
    """
    Returns coins passing simple price filters plus some key fields.
    Tune further filters in-place as needed.
    """
    coins = fetch_from_coingecko()
    results: List[Dict[str, Any]] = []

    for coin in coins:
        try:
            price = coin.get("current_price")
            if price is None:
                continue

            if min_price <= float(price) <= max_price:
                results.append(
                    {
                        "symbol": coin.get("symbol"),
                        "name": coin.get("name"),
                        "price": price,
                        "volume": coin.get("total_volume"),
                        "market_cap": coin.get("market_cap"),
                        "id": coin.get("id"),
                    }
                )
        except Exception as e:
            logger.error("Error processing coin %s: %s", coin.get("id"), e)

    logger.info("Coins passing filters: %d (min=%s, max=%s)", len(results), min_price, max_price)
    return JSONResponse(content=results)

if __name__ == "__main__":
    # For local runs: respects Render's $PORT if present
    import uvicorn
    port = int(os.environ.get("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
