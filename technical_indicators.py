# technical_indicators.py
import pandas as pd
import numpy as np

def compute_rsi(data, period: int = 14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / (avg_loss + 1e-9)  # avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def compute_ema(data, span: int):
    return data['close'].ewm(span=span, adjust=False).mean().iloc[-1]

def compute_vwap(data):
    return (data['close'] * data['volume']).cumsum().iloc[-1] / data['volume'].cumsum().iloc[-1]

def compute_atr(data, period: int = 14):
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr.iloc[-1]

def compute_rvol(data, period: int = 20):
    avg_volume = data['volume'].rolling(period).mean().iloc[-1]
    return data['volume'].iloc[-1] / (avg_volume + 1e-9)

def compute_technical_metrics(data: pd.DataFrame):
    """
    Input: DataFrame with columns ['open','high','low','close','volume']
    Output: dict of computed indicators
    """
    return {
        "EMA5": compute_ema(data, 5),
        "EMA13": compute_ema(data, 13),
        "EMA50": compute_ema(data, 50),
        "RSI": compute_rsi(data, 14),
        "VWAP": compute_vwap(data),
        "ATR": compute_atr(data, 14),
        "RVOL": compute_rvol(data, 20),
        "Volume": data['volume'].iloc[-1],
        "PriceChangePct": ((data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2]) * 100
    }
