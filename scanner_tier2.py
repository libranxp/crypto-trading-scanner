# scanner_tier2.py
from technical_indicators import compute_technical_metrics
import pandas as pd

def tier2_scan(ticker_data):
    metrics = compute_technical_metrics(ticker_data)
    # Example stricter filter
    if metrics['RSI'] > 60 and metrics['RVOL'] > 1.5 and metrics['EMA_alignment']:
        return metrics
    return None

if __name__ == "__main__":
    df = pd.DataFrame({
        'open': [100, 102, 101, 105],
        'high': [102, 104, 103, 106],
        'low': [99, 100, 100, 104],
        'close': [101, 103, 102, 105],
        'volume': [1000, 1500, 1200, 2000]
    })

    result = tier2_scan(df)
    if result:
        print("✅ Tier 2 Scan Passed:", result)
    else:
        print("❌ Tier 2 Scan No Signal")
