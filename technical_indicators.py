from typing import Dict, List
import math

def _sma(series: List[float], length: int) -> float:
    if len(series) < length or length <= 0: return float("nan")
    return sum(series[-length:]) / float(length)

def _ema(series: List[float], length: int) -> float:
    if len(series) < length or length <= 0: return float("nan")
    k = 2 / (length + 1)
    ema_val = series[0]
    for price in series[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def _rsi(closes: List[float], length: int = 14) -> float:
    if len(closes) < length + 1: return float("nan")
    gains, losses = 0.0, 0.0
    for i in range(-length, 0):
        ch = closes[i] - closes[i - 1]
        if ch > 0: gains += ch
        else: losses += -ch
    if losses == 0: return 100.0
    rs = (gains / length) / (losses / length)
    return 100 - (100 / (1 + rs))

def _atr(highs: List[float], lows: List[float], closes: List[float], length: int = 14) -> float:
    if len(closes) < length + 1: return float("nan")
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    # Use SMA of TR for simplicity
    if len(trs) < length: return float("nan")
    return sum(trs[-length:]) / float(length)

def _vwap(ohlcv: List[Dict]) -> float:
    pv_sum, vol_sum = 0.0, 0.0
    for c in ohlcv:
        # Typical price
        tp = (c["h"] + c["l"] + c["c"]) / 3.0
        v = c["v"] or 0.0
        pv_sum += tp * v
        vol_sum += v
    return pv_sum / vol_sum if vol_sum > 0 else float("nan")

def _rvol(volumes: List[float], lookback: int = 20) -> float:
    if len(volumes) < lookback + 1: return float("nan")
    recent = volumes[-1]
    base = sum(volumes[-(lookback+1):-1]) / float(lookback)
    return recent / base if base > 0 else float("nan")

def compute_technical_metrics(ohlcv: List[Dict]) -> Dict:
    """Return RSI, EMAs, VWAP, ATR, RVOL, last close & volume."""
    if not ohlcv or len(ohlcv) < 30:
        return {}
    closes = [c["c"] for c in ohlcv]
    highs = [c["h"] for c in ohlcv]
    lows = [c["l"] for c in ohlcv]
    vols = [c["v"] for c in ohlcv]

    rsi = _rsi(closes, 14)
    ema5 = _ema(closes, 5)
    ema13 = _ema(closes, 13)
    ema50 = _ema(closes, 50)
    vwap = _vwap(ohlcv)
    atr = _atr(highs, lows, closes, 14)
    rvol = _rvol(vols, 20)

    return {
        "rsi": rsi,
        "ema5": ema5,
        "ema13": ema13,
        "ema50": ema50,
        "vwap": vwap,
        "atr": atr,
        "rvol": rvol,
        "close": closes[-1],
        "volume": vols[-1],
    }
