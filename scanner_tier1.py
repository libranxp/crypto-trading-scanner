import os
import requests
import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# Load environment variables
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

def get_coingecko_market():
    """Fetch coins from CoinGecko market data"""
    url = f"{COINGECKO_API_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False
    }
    resp = requests.get(url, params=params, timeout=30)
    return resp.json()

def get_cmc_data(symbol):
    """Fetch market cap + volume from CoinMarketCap"""
    try:
        headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        resp = requests.get(url, params={"symbol": symbol}, headers=headers, timeout=30)
        data = resp.json()["data"].get(symbol.upper(), {})
        return {
            "market_cap": data.get("quote", {}).get("USD", {}).get("market_cap", 0),
            "volume": data.get("quote", {}).get("USD", {}).get("volume_24h", 0)
        }
    except Exception:
        return {"market_cap": 0, "volume": 0}

def get_messari_metrics(symbol):
    """Fetch metrics from Messari"""
    try:
        headers = {"x-messari-api-key": MESSARI_API_KEY}
        url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json().get("data", {})
        return {
            "rsi": data.get("market_data", {}).get("rsi", 55),
            "rvol": data.get("market_data", {}).get("real_volume_last_24_hours", 2)
        }
    except Exception:
        return {"rsi": 55, "rvol": 2}

def tier1_scan():
    logging.info("🔍 Running Tier 1 Scan...")
    candidates = []
    coins = get_coingecko_market()

    for coin in coins:
        price = coin.get("current_price", 0)
        market_cap = coin.get("market_cap", 0)
        volume = coin.get("total_volume", 0)
        price_change = coin.get("price_change_percentage_24h", 0)

        # Apply lightweight filters
        if not (0.005 <= price <= 50): continue
        if not (20_000_000 <= market_cap <= 2_000_000_000): continue
        if volume < 15_000_000: continue
        if not (2 <= price_change <= 15): continue

        cmc_data = get_cmc_data(coin["symbol"])
        messari_data = get_messari_metrics(coin["symbol"])

        candidate = {
            "name": coin["name"],
            "symbol": coin["symbol"],
            "price": price,
            "market_cap": cmc_data["market_cap"] or market_cap,
            "volume": cmc_data["volume"] or volume,
            "price_change": price_change,
            "rsi": messari_data["rsi"],
            "rvol": messari_data["rvol"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        candidates.append(candidate)

    if candidates:
        logging.info(f"✅ {len(candidates)} candidates found")
        supabase.table("tier1_results").insert(candidates).execute()
    else:
        logging.info("⚠️ No candidates found in Tier 1 scan.")

    return candidates

if __name__ == "__main__":
    tier1_scan()
