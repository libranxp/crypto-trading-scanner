# services/scanner.py
from technical_indicators import compute_technical_metrics

def run_auto_scan(df):
    """
    Runs Tier 1 auto scan on given OHLCV DataFrame.
    Returns metrics dict if conditions met, else None.
    """
    metrics = compute_technical_metrics(df)
    if 50 <= metrics['RSI'] <= 70 and metrics['EMA_alignment']:
        return metrics
    return None
