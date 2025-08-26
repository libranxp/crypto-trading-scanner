import pandas as pd

def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_atr(high, low, close, period=14):
    data = pd.DataFrame({"high": high, "low": low, "close": close})
    data["h-l"] = data["high"] - data["low"]
    data["h-c"] = abs(data["high"] - data["close"].shift())
    data["l-c"] = abs(data["low"] - data["close"].shift())
    tr = data[["h-l", "h-c", "l-c"]].max(axis=1)
    return tr.rolling(period).mean()

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()
