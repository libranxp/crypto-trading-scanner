import os, sys, requests
from telegram_alerts import send_telegram

CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")

def fetch_market_data():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    resp = requests.get(url, headers=headers, params={"limit": 100, "convert": "USD"})
    resp.raise_for_status()
    return resp.json()["data"]

def filter_symbols(data):
    selected = []
    for coin in data:
        price = coin["quote"]["USD"]["price"]
        vol = coin["quote"]["USD"]["volume_24h"]
        change = coin["quote"]["USD"]["percent_change_24h"]
        if 2 <= price <= 15 and change > 5 and vol > 1_000_000:
            selected.append(coin["symbol"])
    return selected

if __name__ == "__main__":
    outfile = "tier1_symbols.txt"
    if "--out" in sys.argv:
        outfile = sys.argv[sys.argv.index("--out") + 1]

    try:
        data = fetch_market_data()
        symbols = filter_symbols(data)
        with open(outfile, "w") as f:
            f.write(",".join(symbols))

        if symbols:
            send_telegram(f"[Tier1 Alert] Symbols found: {', '.join(symbols)}")
        else:
            send_telegram("[Tier1 Alert] No symbols matched this cycle.")
    except Exception as e:
        send_telegram(f"[Tier1 Error] {e}")
