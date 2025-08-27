import pandas as pd
import numpy as np

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def compute_vwap(df):
    return (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

def compute_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def compute_rvol(df, period=14):
    avg_vol = df['Volume'].rolling(period).mean()
    return df['Volume'] / avg_vol

# ✅ Unified function for scanner_tier2
def compute_metrics(df):
    """
    Returns dict of metrics: RSI, EMA5/13/50, VWAP, ATR, RVOL
    """
    df = df.copy()
    metrics = {}

    metrics['RSI'] = compute_rsi(df['Close']).iloc[-1]
    metrics['EMA5'] = compute_ema(df['Close'], 5).iloc[-1]
    metrics['EMA13'] = compute_ema(df['Close'], 13).iloc[-1]
    metrics['EMA50'] = compute_ema(df['Close'], 50).iloc[-1]
    metrics['VWAP'] = compute_vwap(df).iloc[-1]
    metrics['ATR'] = compute_atr(df).iloc[-1]
    metrics['RVOL'] = compute_rvol(df).iloc[-1]

    return metrics
