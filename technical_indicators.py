import requests
import numpy as np
import pandas as pd
import logging
from typing import Optional, Tuple
from config import COINGECKO_API_URL

logger = logging.getLogger(__name__)

def fetch_market_chart(coin_id: str, vs_currency="usd", days=2) -> Optional[dict]:
    """
    Use CoinGecko /coins/{id}/market_chart to fetch price and volume history.
    This returns 'prices', 'market_caps', 'total_volumes' arrays.
    """
    try:
        url = f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": vs_currency, "days": days}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.exception("market_chart failed")
        return None

def calculate_rsi_from_prices(prices: list, period: int = 14) -> float:
    """
    prices: list of [timestamp, price]
    Returns last RSI value (simple Wilder's smoothing).
    """
    try:
        if not prices or len(prices) < period + 1:
            return 60.0
        # extract just price numbers
        p = np.array([p[1] for p in prices])
        deltas = np.diff(p)
        ups = np.where(deltas > 0, deltas, 0.0)
        downs = np.where(deltas < 0, -deltas, 0.0)
        # Wilder smoothing
        roll_up = pd.Series(ups).rolling(window=period).mean().iloc[-1]
        roll_down = pd.Series(downs).rolling(window=period).mean().iloc[-1]
        if roll_down == 0:
            return 100.0
        rs = roll_up / roll_down
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi)
    except Exception:
        return 60.0

def calculate_rvol_from_volumes(volumes: list) -> float:
    """
    volumes: list of [timestamp, volume]
    RVOL defined here as latest_volume / average(volume[-(n+1):-1])
    """
    try:
        if not volumes or len(volumes) < 3:
            return 1.0
        v = np.array([vv[1] for vv in volumes])
        latest = v[-1]
        # average of previous N (choose 24 if available)
        n = min(24, len(v)-1)
        avg_prev = v[-1-n:-1].mean() if n > 0 else v[:-1].mean()
        if avg_prev == 0:
            return 1.0
        return float(latest / avg_prev)
    except Exception:
        return 1.0

def compute_technical_metrics(coin_id: str, current_price: float) -> dict:
    """
    Returns a dictionary: rsi, rvol, ema_aligned (simple), vwap_proximity
    """
    chart = fetch_market_chart(coin_id, days=3)
    metrics = {"rsi": 60.0, "rvol": 1.0, "ema_aligned": False, "vwap_proximity": 0.0}
    if not chart:
        return metrics

    prices = chart.get("prices", [])
    volumes = chart.get("total_volumes", [])
    metrics["rsi"] = calculate_rsi_from_prices(prices)
    metrics["rvol"] = calculate_rvol_from_volumes(volumes)

    # Simple EMA alignment check using recent prices (not ideal but inexpensive)
    try:
        p = pd.Series([pr[1] for pr in prices])
        ema5 = p.ewm(span=5, adjust=False).mean().iloc[-1]
        ema13 = p.ewm(span=13, adjust=False).mean().iloc[-1]
        ema50 = p.ewm(span=50, adjust=False).mean().iloc[-1]
        metrics["ema_aligned"] = (ema5 > ema13 > ema50)
        # approximate VWAP over the fetched data: sum(price * vol)/sum(vol)
        vol_arr = np.array([vv[1] for vv in volumes])
        price_arr = np.array([pr[1] for pr in prices])
        if vol_arr.sum() > 0:
            vwap = (price_arr * vol_arr[:len(price_arr)]).sum() / vol_arr.sum()
            metrics["vwap_proximity"] = abs(current_price - vwap) / vwap if vwap != 0 else 0.0
    except Exception:
        pass

    return metrics
