import argparse
import pandas as pd
from services.providers import get_historical_data
from technical_indicators import compute_metrics

def analyze_symbol(symbol):
    df = get_historical_data(symbol)  # must return OHLCV DataFrame
    if df is None or df.empty:
        return None
    
    metrics = compute_metrics(df)

    # Apply your strict scanner criteria
    price = df['Close'].iloc[-1]
    change_pct = (price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
    volume = df['Volume'].iloc[-1]

    # ✅ Criteria checks
    if not (0.001 <= price <= 100): return None
    if not (2 <= change_pct <= 20): return None
    if metrics['RSI'] < 50 or metrics['RSI'] > 70: return None
    if metrics['RVOL'] < 2: return None
    if not (metrics['EMA5'] > metrics['EMA13'] > metrics['EMA50']): return None
    if abs(price - metrics['VWAP']) / metrics['VWAP'] > 0.02: return None

    return {
        "symbol": symbol,
        "price": round(price, 4),
        "change_pct": round(change_pct, 2),
        **metrics
    }

def main(symbols=None):
    results = []
    if symbols:
        for sym in symbols.split(","):
            data = analyze_symbol(sym.strip())
            if data:
                results.append(data)
    else:
        # fallback: Tier 1 feed or Supabase later
        print("No symbols passed to Tier 2 scanner")

    if results:
        df = pd.DataFrame(results)
        print(df.to_string(index=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=str, help="Comma-separated symbols to scan")
    args = parser.parse_args()
    main(args.symbols)
