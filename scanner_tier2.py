import os, sys, requests
from telegram_alerts import send_telegram
from technical_indicators import compute_rsi, ema
from db import supabase

CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")

def fetch_coin(symbol):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    resp = requests.get(url, headers=headers, params={"symbol": symbol})
    resp.raise_for_status()
    return resp.json()["data"][symbol]

def analyze(symbol):
    coin = fetch_coin(symbol)
    price = coin["quote"]["USD"]["price"]

    # Placeholder RSI & EMA signals (real RSI requires OHLC candles)
    rsi = 55
    ema_signal = "Bullish" if rsi > 50 else "Bearish"
    catalyst = "Pending"
    risk = "Medium"

    # Push to Supabase
    supabase.table("scanner_results").insert({
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "ema_signal": ema_signal,
        "catalyst": catalyst,
        "risk": risk
    }).execute()

    # Telegram alert
    msg = (
        f"[Tier2 Alert] {symbol}\n"
        f"Price: ${price:,.2f}\n"
        f"RSI: {rsi} | EMA: {ema_signal}\n"
        f"Catalyst: {catalyst}\n"
        f"Risk: {risk}"
    )
    send_telegram(msg)

if __name__ == "__main__":
    if "--symbols" in sys.argv:
        symbols = sys.argv[sys.argv.index("--symbols") + 1].split(",")
    else:
        with open("tier1_symbols.txt") as f:
            symbols = f.read().split(",")

    for sym in symbols:
        if not sym.strip():
            continue
        try:
            analyze(sym.strip())
        except Exception as e:
            send_telegram(f"[Tier2 Error] {sym}: {e}")
