# scanner_tier2.py
import os
import requests
import pandas as pd
from technical_indicators import compute_technical_metrics
from telegram_alerts import send_telegram_alert

# --- ENVIRONMENT VARIABLES ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# --- FETCH CANDLE DATA (Polygon.io Example) ---
def fetch_ohlcv(symbol: str, timespan="minute", limit=200):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/{timespan}/2025-01-01/2025-01-02"
    params = {"adjusted": "true", "limit": limit, "apiKey": POLYGON_API_KEY}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json().get("results", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    return df[["open","high","low","close","volume"]]

# --- AI SCORING LOGIC ---
def ai_score(metrics: dict, sentiment_score: float, catalyst_score: float):
    score = 0
    if metrics["RSI"] > 50 and metrics["RSI"] < 70: score += 2
    if metrics["EMA5"] > metrics["EMA13"] > metrics["EMA50"]: score += 2
    if metrics["RVOL"] > 2: score += 2
    if sentiment_score >= 0.6: score += 2
    if catalyst_score >= 0.5: score += 2
    return round(min(score, 10), 1)

def risk_assessment(metrics, price):
    sl = round(price - metrics["ATR"], 4)
    tp = round(price + (metrics["ATR"] * 2), 4)
    position_size = 100  # placeholder logic
    return {"SL": sl, "TP": tp, "Size": position_size}

# --- MAIN TIER 2 SCANNER ---
def run_tier2(symbol: str):
    df = fetch_ohlcv(symbol)
    if df.empty:
        print(f"No data for {symbol}")
        return

    metrics = compute_technical_metrics(df)
    sentiment_score = 0.7  # integrate real sentiment provider here
    catalyst_score = 0.6   # integrate catalyst detection here

    ai = ai_score(metrics, sentiment_score, catalyst_score)
    risk = risk_assessment(metrics, df['close'].iloc[-1])

    alert_msg = f"""
🚨 New Signal: {symbol}

📈 Price: ${df['close'].iloc[-1]:.4f} | Change: {metrics['PriceChangePct']:.2f}%
📊 AI Score: {ai}/10 (Confidence)
🧠 Reason: EMA alignment + RSI {metrics['RSI']:.1f} + RVOL {metrics['RVOL']:.2f}
📍 Risk: SL = ${risk['SL']} | TP = ${risk['TP']} | Size = ${risk['Size']}
📡 Sentiment: {sentiment_score:.2f} | Catalyst: {catalyst_score:.2f}

🔗 [TradingView Chart](https://www.tradingview.com/symbols/{symbol})
🔗 [News Source](https://newsapi.org)
🔗 [Reddit](https://reddit.com/r/cryptocurrency)
🔗 [Tweet](https://twitter.com/search?q={symbol})

📅 Time: Auto Scan
"""

    send_telegram_alert(alert_msg)

if __name__ == "__main__":
    # Example: scan top crypto symbols from Supabase or API
    symbols = ["BTCUSD", "ETHUSD"]  # replace with live fetched list
    for sym in symbols:
        run_tier2(sym)
