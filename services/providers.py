# services/providers.py
import requests
import logging
import pandas as pd
from typing import List

COINGECKO_API = "https://api.coingecko.com/api/v3"

def get_top_markets(limit: int = 200, vs_currency: str = "usd") -> List[dict]:
    """Return coin market objects from CoinGecko (id, symbol, name, current_price, market_cap, total_volume, price_change_percentage_24h)."""
    url = f"{COINGECKO_API}/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False,
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def get_ohlcv_coin_gecko(coin_id: str, days: int = 7) -> pd.DataFrame:
    """
    Return a DataFrame with columns: close, volume, high, low indexed by timestamp.
    Uses /coins/{id}/market_chart endpoint (prices + volumes).
    """
    url = f"{COINGECKO_API}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])
    if not prices:
        return pd.DataFrame()

    # Align prices and volumes by index
    import pandas as pd
    ts = [int(p[0] / 1000) for p in prices]
    closes = [p[1] for p in prices]
    vols = [v[1] for v in volumes] if volumes else [0] * len(closes)
    df = pd.DataFrame({"close": closes, "volume": vols}, index=pd.to_datetime(ts, unit="s"))
    # approximate high/low
    df["high"] = df["close"] * 1.001
    df["low"] = df["close"] * 0.999
    return df

def get_current_price_for_symbol(symbol: str, vs_currency: str = "usd") -> float:
    """
    Symbol should be CoinGecko coin id or symbol; this helper fetches current price for an id.
    Prefer coin id. For symbol lookup you'd map from get_top_markets results.
    """
    url = f"{COINGECKO_API}/simple/price"
    params = {"ids": symbol, "vs_currencies": vs_currency, "include_24hr_change": "true"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get(symbol, {}).get(vs_currency)
