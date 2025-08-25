# scanner_tier1.py
from services.scanner import run_auto_scan
from technical_indicators import rsi, ema, atr, vwap, rvol, ema_alignment, compute_technical_metrics
import pandas as pd

def tier1_scan(ticker_data):
    metrics = compute_technical_metrics(ticker_data)
    # Add your Tier 1 lightweight filters here
    if metrics['RSI'] >= 50 and metrics['RSI'] <= 70 and metrics['EMA_alignment']:
        return metrics
    return None

if __name__ == "__main__":
    # Example live fetch logic (replace with actual API calls)
    # For testing purposes, create dummy OHLCV DataFrame
    df = pd.DataFrame({
        'open': [100, 102, 101, 105],
        'high': [102, 104, 103, 106],
        'low': [99, 100, 100, 104],
        'close': [101, 103, 102, 105],
        'volume': [1000, 1500, 1200, 1300]
    })
    result = tier1_scan(df)
    if result:
        print("Tier 1 Scan Passed:", result)
    else:
        print("Tier 1 Scan No Signal")
