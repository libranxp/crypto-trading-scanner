import requests
from config import COINGECKO_API_URL, LUNARCRUSH_API_URL, LUNARCRUSH_API_KEY

def tier1_scan():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False
    }
    try:
        response = requests.get(f"{COINGECKO_API_URL}/coins/markets", params=params)
        response.raise_for_status()
        coins = response.json()
    except Exception as e:
        print(f"CoinGecko fetch failed: {e}")
        return []

    results = []
    for coin in coins:
        price = coin.get("current_price", 0)
        volume = coin.get("total_volume", 0)
        market_cap = coin.get("market_cap", 0)
        symbol = coin.get("symbol", "").upper()
        name = coin.get("name", "")

        if not (0.001 <= price <= 100): continue
        if volume <= 10_000_000: continue
        if not (10_000_000 <= market_cap <= 5_000_000_000): continue

        sentiment_score = 0
        try:
            params = {"symbol": symbol}
            headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
            resp = requests.get(f"{LUNARCRUSH_API_URL}/assets", params=params, headers=headers)
            data = resp.json()
            if data["data"]:
                sentiment_score = data["data"][0].get("galaxy_score", 0)
        except Exception:
            pass

        if sentiment_score < 0.6: continue

        results.append({
            "name": name,
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "market_cap": market_cap,
            "sentiment_score": sentiment_score
        })

    return results
