# technical_indicators.py
import pandas as pd
import numpy as np

def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Input: df with columns ['close','high','low','volume'] indexed by timestamp.
    Output: dictionary {rsi, ema5, ema13, ema50, vwap, atr, rvol, volume}
    """
    if df is None or df.empty:
        return {}

    close = df["close"].astype(float)
    high = df.get("high", close).astype(float)
    low = df.get("low", close).astype(float)
    volume = df.get("volume", pd.Series([0] * len(df), index=df.index)).astype(float)

    # EMAs
    def ema(series, span):
        return series.ewm(span=span, adjust=False).mean()

    ema5 = ema(close, 5).iloc[-1] if len(close) >= 1 else None
    ema13 = ema(close, 13).iloc[-1] if len(close) >= 1 else None
    ema50 = ema(close, 50).iloc[-1] if len(close) >= 1 else None

    # RSI (14)
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.ewm(alpha=1/14, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-9)
    rsi_series = 100 - (100 / (1 + rs))
    rsi = rsi_series.iloc[-1] if not rsi_series.empty else None

    # VWAP
    typical_price = (high + low + close) / 3.0
    cum_vol = volume.cumsum()
    vwap_series = (typical_price * volume).cumsum() / (cum_vol + 1e-9)
    vwap = vwap_series.iloc[-1] if not vwap_series.empty else None

    # ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1] if len(tr) >= 14 else tr.mean()

    # RVOL
    avg_vol = volume.mean() if len(volume) > 0 else 0
    recent_vol = volume.iloc[-14:].mean() if len(volume) >= 14 else volume.mean()
    rvol = (recent_vol / (avg_vol + 1e-9)) if avg_vol > 0 else 0

    metrics = {
        "rsi": float(rsi) if rsi is not None and not pd.isna(rsi) else None,
        "ema5": float(ema5) if ema5 is not None and not pd.isna(ema5) else None,
        "ema13": float(ema13) if ema13 is not None and not pd.isna(ema13) else None,
        "ema50": float(ema50) if ema50 is not None and not pd.isna(ema50) else None,
        "vwap": float(vwap) if vwap is not None and not pd.isna(vwap) else None,
        "atr": float(atr) if atr is not None and not pd.isna(atr) else None,
        "rvol": float(rvol) if rvol is not None and not pd.isna(rvol) else None,
        "volume": float(volume.iloc[-1]) if len(volume) > 0 else None,
    }
    return metrics
