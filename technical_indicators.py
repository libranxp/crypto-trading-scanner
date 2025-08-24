import math
import requests
import pandas as pd
from datetime import datetime, timezone
from config import COINGECKO_API_URL

def _fetch_ohlc(symbol_id: str, days: int = 7):
    url = f"{COINGECKO_API_URL}/coins/{symbol_id}/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "hourly"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])
    df = pd.DataFrame(prices, columns=["ts", "price"])
    df["volume"] = [v[1] for v in volumes] if len(volumes) == len(prices) else 0
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df

def rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 1e-9)
    rsi_val = 100 - (100 / (1 + rs))
    return float(rsi_val.iloc[-1])

def ema(series: pd.Series, span: int) -> float:
    return float(series.ewm(span=span, adjust=False).mean().iloc[-1])

def ema_alignment(close: pd.Series) -> bool:
    ema5 = ema(close, 5)
    ema13 = ema(close, 13)
    ema50 = ema(close, 50)
    return ema5 > ema13 > ema50

def rvol(df: pd.DataFrame, window:int=24) -> float:
    # last hour volume vs mean of previous hours
    if len(df) < window + 1:
        return 1.0
    last = df["volume"].iloc[-1]
    base = df["volume"].iloc[-(window+1):-1].mean()
    return float(last / (base or 1e-9))

def vwap_proximity(df: pd.DataFrame) -> float:
    # hourly VWAP over last 24h
    d = df.tail(24)
    if d["volume"].sum() == 0:
        return 1.0
    vwap = (d["price"] * d["volume"]).sum() / d["volume"].sum()
    last_price = float(d["price"].iloc[-1])
    return abs(last_price - vwap) / vwap

def pump_filter(df: pd.DataFrame) -> bool:
    # reject if >50% spike in <1h with low volume (approx using last 2 bars)
    if len(df) < 3:
        return False
    p_now = df["price"].iloc[-1]
    p_prev = df["price"].iloc[-2]
    vol_now = df["volume"].iloc[-1]
    vol_prev = df["volume"].iloc[-2]
    spike = (p_now - p_prev) / (p_prev or 1e-9)
    low_vol = vol_now < (vol_prev * 0.5)
    return (spike > 0.50) and low_vol

def compute_all(symbol_id: str):
    df = _fetch_ohlc(symbol_id, days=7)
    close = df["price"]
    return {
        "rsi": rsi(close),
        "ema_aligned": ema_alignment(close),
        "rvol": rvol(df),
        "vwap_proximity": vwap_proximity(df),
        "pump_reject": pump_filter(df),
        "last_price": float(close.iloc[-1]),
        "last_ts": df["ts"].iloc[-1].isoformat()
    }
