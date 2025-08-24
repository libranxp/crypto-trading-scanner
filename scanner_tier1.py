import logging
import os
import requests
from config import (
    ALPHAVANTAGE_API_KEY,
    COINMARKETCAP_API_KEY,
    LUNARCRUSH_API_KEY,
    MESSARI_API_KEY,
    POLYGON_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY
)
from supabase import create_client

# Setup Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

# -------------------------------
# API HELPERS
# -------------------------------
def fetch_coinmarketcap():
    """Fetch top coins from CoinMarketCap."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    try:
        r = requests.get(url, headers=headers, params={"limit": 100, "convert": "USD"}, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        logging.error(f"❌ CMC fetch failed: {e}")
        return []

def fetch_lunarcrush():
    """Fetch trending coins from LunarCrush."""
    url = f"https://lunarcrush.com/api3/coins?data=market&key={LUNARCRUSH_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        logging.error(f"❌ LunarCrush fetch failed: {e}")
        return []

def fetch_messari():
    """Fetch market data from Messari."""
    url = "https://data.messari.io/api/v1/assets"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        logging.error(f"❌ Messari fetch failed: {e}")
        return []

# -------------------------------
# FILTER LOGIC
# -------------------------------
def filter_coins(data, source="CMC"):
    """Apply lightweight filters across sources."""
    results = []
    for c in data:
        try:
            if source == "CMC":
                symbol = c.get("symbol")
                price = c["quote"]["USD"]["price"]
                volume = c["quote"]["USD"]["volume_24h"]
                market_cap = c["quote"]["USD"]["market_cap"]
                change_24h = c["quote"]["USD"]["percent_change_24h"]
            elif source == "LUNAR":
                symbol = c.get("s")
                price = c.get("p")
                volume = c.get("v")
                market_cap = c.get("mc")
                change_24h = c.get("pchg")
            elif source == "MESSARI":
                symbol = c.get("symbol")
                metrics = c.get("metrics", {})
                price = metrics.get("market_data", {}).get("price_usd")
                volume = metrics.get("market_data", {}).get("volume_last_24_hours")
                market_cap = metrics.get("marketcap", {}).get("current_marketcap_usd")
                change_24h = metrics.get("market_data", {}).get("percent_change_usd_last_24_hours")
            else:
                continue

            # Lightweight filters
            if price and 0.01 < price < 500:  # reasonable tradable range
                if volume and volume > 1_000_000 and market_cap and market_cap < 2_000_000_000:
                    results.append({
                        "symbol": symbol,
                        "price": price,
                        "market_cap": market_cap,
                        "volume": volume,
                        "change_24h": change_24h,
                        "source": source
                    })
        except Exception:
            continue
    return results

# -------------------------------
# SUPABASE STORAGE
# -------------------------------
def save_to_supabase(results):
    try:
        if results:
            supabase.table("scanner_results").insert(results).execute()
            logging.info(f"✅ Saved {len(results)} results to Supabase.")
    except Exception as e:
        logging.error(f"❌ Supabase insert failed: {e}")

# -------------------------------
# MAIN PIPELINE
# -------------------------------
def run_tier1_scan():
    logging.info("🚀 Running Tier 1 Scan...")

    all_results = []

    cmc = fetch_coinmarketcap()
    all_results += filter_coins(cmc, "CMC")

    lunar = fetch_lunarcrush()
    all_results += filter_coins(lunar, "LUNAR")

    messari = fetch_messari()
    all_results += filter_coins(messari, "MESSARI")

    save_to_supabase(all_results)
    return all_results

if __name__ == "__main__":
    run_tier1_scan()
