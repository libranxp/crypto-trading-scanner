import requests
from datetime import datetime, timezone
from config import COINGECKO_API_URL, TIER1_CACHE_FILE
from technical_indicators import compute_all

# Filters as per your spec
PRICE_MIN, PRICE_MAX = 0.005, 50
MCAP_MIN, MCAP_MAX = 20_000_000, 2_000_000_000
VOL_MIN = 15_000_000
CHANGE_MIN, CHANGE_MAX = 2, 15  # %
VWAP_MAX_DIST = 0.02  # 2%
RSI_MIN, RSI_MAX = 50, 70
RVOL_MIN = 2.0

def _fetch_market_page(page: int):
    url = f"{COINGECKO_API_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 250,
        "page": page,
        "sparkline": False
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def run_tier1():
    results = []
    # we grab top 500 by volume (2 pages)
    all_coins = _fetch_market_page(1) + _fetch_market_page(2)
    for c in all_coins:
        price = c.get("current_price") or 0
        mcap = c.get("market_cap") or 0
        vol = c.get("total_volume") or 0
        chg = c.get("price_change_percentage_24h") or 0

        if not (PRICE_MIN <= price <= PRICE_MAX):        continue
        if not (MCAP_MIN <= mcap <= MCAP_MAX):           continue
        if vol < VOL_MIN:                                 continue
        if not (CHANGE_MIN <= chg <= CHANGE_MAX):         continue

        # compute technicals from OHLC
        tid = c["id"]  # coingecko unique id
        tech = compute_all(tid)
        if not (RSI_MIN <= tech["rsi"] <= RSI_MAX):       continue
        if tech["rvol"] < RVOL_MIN:                       continue
        if not tech["ema_aligned"]:                       continue
        if tech["vwap_proximity"] > VWAP_MAX_DIST:        continue
        if tech["pump_reject"]:                           continue

        results.append({
            "name": c["name"],
            "symbol": c["symbol"].upper(),
            "coingecko_id": tid,
            "coingecko_url": f"https://www.coingecko.com/en/coins/{tid}",
            "price": float(price),
            "market_cap": int(mcap),
            "volume": int(vol),
            "price_change_24h": float(chg),
            "rsi": tech["rsi"],
            "rvol": tech["rvol"],
            "ema_aligned": tech["ema_aligned"],
            "vwap_proximity": tech["vwap_proximity"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # cache to file for dashboard and Tier 2
    TIER1_CACHE_FILE.write_text(__import__("json").dumps({"results": results}, indent=2))
    return results
