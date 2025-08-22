import requests
from config import ALPHAVANTAGE_API_URL, ALPHAVANTAGE_API_KEY, COINGECKO_API_URL

def calculate_rsi(symbol):
    # Example: Fetch RSI from AlphaVantage (daily)
    try:
        params = {
            "function": "RSI",
            "symbol": symbol.upper(),
            "interval": "daily",
            "time_period": 14,
            "series_type": "close",
            "apikey": ALPHAVANTAGE_API_KEY
        }
        response = requests.get(ALPHAVANTAGE_API_URL, params=params)
        data = response.json()
        rsi_values = list(data.get("Technical Analysis: RSI", {}).values())
        if rsi_values:
            return float(rsi_values[0])
    except Exception:
        pass
    # Fallback or default
    return 60

def calculate_ema_alignment(symbol):
    # Placeholder: Assume EMA5 > EMA13 > EMA50 is True for demo
    return True

def calculate_vwap_proximity(symbol, current_price):
    # Placeholder: Return 1% proximity for demo
    return 0.01

def calculate_rvol(symbol):
    # Placeholder: Return 2.5x relative volume for demo
    return 2.5
