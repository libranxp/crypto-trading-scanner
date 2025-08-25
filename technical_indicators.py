# technical_indicators.py
import math
from typing import List, Dict

def ema(series: List[float], period: int) -> List[float]:
    if not series or period <= 0:
        return []
    k = 2 / (period + 1)
    ema_vals = []
    ema_prev = series[0]
    ema_vals.append(ema_prev)
    for price in series[1:]:
        ema_prev = price * k + ema_prev * (1 - k)
        ema_vals.append(ema_prev)
    return ema_vals

def rsi(prices: List[float], period: int = 14) -> List[float]:
    if len(prices) < period + 1:
        return []
    gains, losses = [], []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i-1]
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsis = [None] * (period)  # first 'period' values are undefined
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = (avg_gain / avg_loss) if avg_loss != 0 else math.inf
        rsi_val = 100 - (100 / (1 + rs))
        rsis.append(rsi_val)
    return rsis

def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    if len(closes) < period + 1:
        return []
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    # Wilder's smoothing
    atrs = []
    atr_prev = sum(trs[:period]) / period
    atrs.extend([None]*period)
    for i in range(period, len(trs)):
        atr_prev = (atr_prev*(period-1) + trs[i]) / period
        atrs.append(atr_prev)
    return atrs

def vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[float]:
    if not closes or not volumes or len(closes) != len(volumes):
        return []
    cum_pv, cum_v = 0.0, 0.0
    vwaps = []
    for i in range(len(closes)):
        typical = (highs[i] + lows[i] + closes[i]) / 3.0
        pv = typical * volumes[i]
        cum_pv += pv
        cum_v += volumes[i]
        vwaps.append(cum_pv / cum_v if cum_v else None)
    return vwaps

def rvol(volumes: List[float], lookback: int = 20) -> List[float]:
    if len(volumes) < lookback:
        return []
    rv = [None]*(lookback-1)
    for i in range(lookback-1, len(volumes)):
        window = volumes[i-(lookback-1):i+1]
        avg = sum(window)/len(window)
        rv.append(volumes[i]/avg if avg else None)
    return rv

def ema_alignment(ema5: float, ema13: float, ema50: float) -> bool:
    return ema5 is not None and ema13 is not None and ema50 is not None and (ema5 > ema13 > ema50)
