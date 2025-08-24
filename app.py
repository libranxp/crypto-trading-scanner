from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "Crypto Scanner API running"}

@app.get("/scan/auto")
def auto_scan():
    """
    Tier 1 – Lightweight Filters
    Populates dashboard watchlist using low-cost API calls.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": False,
        }
        resp = requests.get(url, params=params, timeout=30)
        coins = resp.json()

        results = []
        for coin in coins:
            if coin.get("market_cap", 0) > 100_000_000 and coin.get("total_volume", 0) > 50_000_000:
                results.append({
                    "name": coin["name"],
                    "symbol": coin["symbol"].upper(),
                    "price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "volume": coin["total_volume"],
                    "price_change_24h": coin.get("price_change_percentage_24h", 0),
                    "rsi": 50,  # placeholder (later from technical_indicators.py)
                    "rvol": 1.0,  # placeholder
                    "coingecko_url": f"https://www.coingecko.com/en/coins/{coin['id']}"
                })

        return JSONResponse({"results": results})

    except Exception as e:
        logging.error(f"❌ Auto scan failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/scan/manual")
def manual_scan():
    """
    Tier 2 – Deep Scan
    Run advanced technical + sentiment + catalyst analysis.
    """
    try:
        # Placeholder response
        results = [{
            "name": "Bitcoin",
            "symbol": "BTC",
            "ai_score": 85,
            "risk": "Medium",
            "sentiment_score": 0.72,
        }]
        return JSONResponse({"results": results})

    except Exception as e:
        logging.error(f"❌ Manual scan failed: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
