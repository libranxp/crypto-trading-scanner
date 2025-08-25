# technical_indicators.py
import pandas as pd

def rsi(df, period: int = 14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(df, period: int = 9):
    return df['close'].ewm(span=period, adjust=False).mean()

def atr(df, period: int = 14):
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = high_low.to_frame(name="hl")
    tr["hc"] = high_close
    tr["lc"] = low_close
    tr_max = tr.max(axis=1)
    return tr_max.rolling(window=period).mean()

def vwap(df):
    pv = (df['close'] * df['volume']).cumsum()
    vol = df['volume'].cumsum()
    return pv / vol

def rvol(df, period: int = 14):
    avg_vol = df['volume'].rolling(window=period).mean()
    return df['volume'] / avg_vol

def ema_alignment(df):
    ema5 = ema(df, 5).iloc[-1]
    ema13 = ema(df, 13).iloc[-1]
    ema21 = ema(df, 21).iloc[-1]
    return ema5 > ema13 > ema21

def compute_technical_metrics(df):
    """Return all computed technical metrics as dict"""
    return {
        "RSI": rsi(df).iloc[-1],
        "EMA5": ema(df, 5).iloc[-1],
        "EMA13": ema(df, 13).iloc[-1],
        "EMA21": ema(df, 21).iloc[-1],
        "ATR": atr(df).iloc[-1],
        "VWAP": vwap(df).iloc[-1],
        "RVOL": rvol(df).iloc[-1],
        "EMA_alignment": ema_alignment(df),
        "last_close": df['close'].iloc[-1]
    }
