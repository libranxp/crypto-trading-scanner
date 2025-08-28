# scanner_tier1.py
import os
import logging
from services.providers import get_top_markets
from db import upsert_signal, supabase

MAX_MARKETS = int(os.getenv("MAX_MARKETS_TO_SCAN", "200"))

# Tier1 lightweight criteria (matches your spec)
MIN_PRICE = 0.001
MAX_PRICE = 100
MIN_VOLUME_24H = 10_000_000  # 10M
MIN_MARKETCAP = 10_000_000
MAX_MARKETCAP = 5_000_000_000
MIN_PRICE_CHANGE_PCT = 2.0
MAX_PRICE_CHANGE_PCT = 20.0

def passes_tier1(market: dict) -> bool:
    try:
        price = float(market.get("current_price") or market.get("price") or 0)
        volume = float(market.get("total_volume") or 0)
        marketcap = float(market.get("market_cap") or 0)
        change24 = float(market.get("price_change_percentage_24h") or 0)
        if not (MIN_PRICE <= price <= MAX_PRICE):
            return False
        if volume < MIN_VOLUME_24H:
            return False
        if not (MIN_MARKETCAP <= marketcap <= MAX_MARKETCAP):
            return False
        if not (MIN_PRICE_CHANGE_PCT <= change24 <= MAX_PRICE_CHANGE_PCT):
            return False
        return True
    except Exception:
        return False

def main():
    logging.info("Running Tier1 scan for up to %d markets", MAX_MARKETS)
    markets = get_top_markets(limit=MAX_MARKETS)
    matches = []
    for m in markets:
        if passes_tier1(m):
            matches.append(m)
            # upsert light summary to supabase for the dashboard/watchlist
            try:
                payload = {
                    "ticker": m.get("symbol", "").upper(),
                    "coin_id": m.get("id"),
                    "name": m.get("name"),
                    "price": m.get("current_price"),
                    "market_cap": m.get("market_cap"),
                    "volume_24h": m.get("total_volume"),
                    "price_change_pct_24h": m.get("price_change_percentage_24h"),
                    "tier": "tier1"
                }
                upsert_signal(payload, on_conflict="coin_id")
            except Exception:
                logging.exception("Failed to upsert tier1 signal")
    # write matches to local file for Tier2 to consume in CI
    with open("tier1_symbols.txt", "w") as f:
        for m in matches:
            f.write(f"{m.get('id')}\n")
    print(f"Tier1: found {len(matches)} matches. Wrote tier1_symbols.txt")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
