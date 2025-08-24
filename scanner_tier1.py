import logging
import requests
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# Setup Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO)

# Example API endpoints (you can add more later)
COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": False
}

def fetch_market_data():
    """Fetch coin data from CoinGecko."""
    try:
        response = requests.get(COINGECKO_API, params=PARAMS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"❌ Failed to fetch market data: {e}")
        return []

def filter_coins(coins):
    """Apply Tier 1 lightweight filters."""
    filtered = []
    for coin in coins:
        price = coin.get("current_price")
        volume = coin.get("total_volume", 0)
        market_cap = coin.get("market_cap", 0)

        # Example filters (tweak as needed)
        if price and 0.01 < price < 200:  # avoid extreme junk and huge coins
            if volume > 1_000_000 and market_cap < 2_000_000_000:
                filtered.append({
                    "name": coin.get("name"),
                    "symbol": coin.get("symbol"),
                    "price": price,
                    "market_cap": market_cap,
                    "volume": volume,
                    "price_change_24h": coin.get("price_change_percentage_24h"),
                    "coingecko_url": f"https://www.coingecko.com/en/coins/{coin.get('id')}"
                })
    return filtered

def save_to_supabase(results):
    """Save scan results into Supabase."""
    try:
        if not results:
            logging.info("⚠️ No results to save.")
            return

        response = supabase.table("scanner_results").insert(results).execute()
        logging.info(f"✅ Saved {len(results)} results to Supabase.")
        return response
    except Exception as e:
        logging.error(f"❌ Failed to save to Supabase: {e}")

def run_tier1_scan():
    """Run Tier 1 scanner pipeline."""
    logging.info("🚀 Running Tier 1 Scan...")
    coins = fetch_market_data()
    filtered = filter_coins(coins)
    save_to_supabase(filtered)
    return filtered

if __name__ == "__main__":
    run_tier1_scan()
