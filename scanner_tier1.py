import requests
import logging
from typing import List
from technical_indicators import compute_technical_metrics
from config import COINGECKO_API_URL

logger = logging.getLogger(__name__)

# Criteria from your brief:
PRICE_MIN = 0.005
PRICE_MAX = 50.0
VOLUME_MIN = 15_000_000  # $15M
PRICE_CHANGE_MIN = 2.0
PRICE_CHANGE_MAX = 15.0
MARKETCAP_MIN = 20_000_000  # $20M
MARKETCAP_MAX = 2_000_000_000  # $2B

def fetch_top_markets(per_page=250, page=1) -> List[dict]:
    url = f"{COINGECKO_API_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": False
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            logger.warning("CoinGecko markets returned non-list payload")
            return []
        return data
    except Exception:
        logger.exception("fetch_top_markets failed")
        return []

def tier1_scan(limit_coins=250):
    """
    Return list of coins that pass the lightweight filters.
    """
    results = []
    coins = fetch_top_markets(per_page=limit_coins, page=1)
    for coin in coins:
        # guard: sometimes API returns e.g. error strings — ensure dict
        if not isinstance(coin, dict):
            logger.warning("Skipping invalid coin entry (not dict): %s", coin)
            continue

        # defensive extraction
        try:
            symbol = (coin.get("symbol") or "").upper()
            name = coin.get("name") or ""
            price = float(coin.get("current_price") or 0.0)
            volume = float(coin.get("total_volume") or 0.0)
            price_change_24h = float(coin.get("price_change_percentage_24h") or 0.0)
            market_cap = float(coin.get("market_cap") or 0.0)
            coin_id = coin.get("id") or ""
            coingecko_url = f"https://www.coingecko.com/en/coins/{coin_id}"
        except Exception:
            logger.exception("Failed to parse coin fields")
            continue

        # filters
        if not (PRICE_MIN <= price <= PRICE_MAX):
            continue
        if volume < VOLUME_MIN:
            continue
        if not (PRICE_CHANGE_MIN <= price_change_24h <= PRICE_CHANGE_MAX):
            continue
        if not (MARKETCAP_MIN <= market_cap <= MARKETCAP_MAX):
            continue

        # compute lightweight technical metrics (cheapish)
        tech = compute_technical_metrics(coin_id, current_price=price)
        rsi = tech.get("rsi", 60.0)
        rvol = tech.get("rvol", 1.0)
        ema_aligned = tech.get("ema_aligned", False)
        vwap_proximity = tech.get("vwap_proximity", 0.0)

        # RSI filter
        if not (50 <= rsi <= 70):
            continue
        if rvol <= 2.0:
            continue
        # VWAP proximity filter ±2% (0.02)
        if vwap_proximity > 0.02:
            continue

        results.append({
            "name": name,
            "symbol": symbol,
            "price": price,
            "market_cap": market_cap,
            "volume": volume,
            "price_change_24h": price_change_24h,
            "rsi": rsi,
            "rvol": rvol,
            "ema_aligned": ema_aligned,
            "vwap_proximity": vwap_proximity,
            "coingecko_url": coingecko_url,
            "id": coin_id
        })

    return results
