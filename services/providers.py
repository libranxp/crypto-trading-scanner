import os
import time
from typing import Dict, List, Optional, Tuple
import requests

EXCHANGE_STABLE = os.getenv("EXCHANGE_STABLE", "USD").upper()
CMC_KEY = os.getenv("COINMARKETCAP_API_KEY")
POLYGON_KEY = os.getenv("POLYGON_API_KEY")
LUNARCRUSH_KEY = os.getenv("LUNARCRUSH_API_KEY")
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "crypto-scanner/1.0"})

def _sleep_smart(seconds: float):
    time.sleep(seconds if seconds > 0 else 0.0)

def get_market_list_cmc(limit: int = 200) -> List[Dict]:
    """Return top markets with price/volume/mcap/percent change. Cost: 1 CMC call."""
    if not CMC_KEY:
        raise RuntimeError("COINMARKETCAP_API_KEY missing")
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {
        "start": 1,
        "limit": max(1, int(limit)),
        "convert": EXCHANGE_STABLE,
        "sort": "volume_24h",
        "cryptocurrency_type": "all",
    }
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    r = SESSION.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    markets = []
    for d in data:
        q = d.get("quote", {}).get(EXCHANGE_STABLE, {}) or {}
        markets.append({
            "symbol": d.get("symbol", "").upper(),
            "name": d.get("name", ""),
            "price": q.get("price"),
            "volume_24h": q.get("volume_24h"),
            "market_cap": q.get("market_cap"),
            "percent_change_24h": q.get("percent_change_24h"),
        })
    return markets

def polygon_symbol(symbol: str) -> str:
    # Polygon crypto format "X:BTCUSD"
    return f"X:{symbol.upper()}{EXCHANGE_STABLE}"

def get_ohlcv_polygon(symbol: str, multiplier: int = 5, timespan: str = "minute",
                      limit: int = 250) -> List[Dict]:
    """Fetch recent OHLCV from Polygon aggregates. Cost: 1 call per symbol."""
    if not POLYGON_KEY:
        raise RuntimeError("POLYGON_API_KEY missing")
    tkr = polygon_symbol(symbol)
    url = f"https://api.polygon.io/v2/aggs/ticker/{tkr}/range/{multiplier}/{timespan}/now/{limit}"
    params = {"adjusted": "true", "sort": "desc", "apiKey": POLYGON_KEY}
    r = SESSION.get(url, params=params, timeout=30)
    if r.status_code == 429:
        _sleep_smart(1.2)
        r = SESSION.get(url, params=params, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", []) or []
    # Return oldest->newest
    return list(reversed([
        {
            "t": x.get("t"),
            "o": x.get("o"),
            "h": x.get("h"),
            "l": x.get("l"),
            "c": x.get("c"),
            "v": x.get("v"),
            "vw": x.get("vw"),  # session vwap (polygon)
        } for x in results
    ]))

def get_social_lunarcrush(symbol: str) -> Dict:
    """Social mentions, engagement, sentiment approx from LunarCrush."""
    if not LUNARCRUSH_KEY:
        return {"mentions": 0, "engagement": 0, "sentiment": 0.0, "influencer": False}
    url = "https://lunarcrush.com/api3/coins"
    params = {"data": "assets", "key": LUNARCRUSH_KEY, "symbol": symbol.upper()}
    r = SESSION.get(url, params=params, timeout=30)
    if r.status_code == 429:
        _sleep_smart(1.2)
        r = SESSION.get(url, params=params, timeout=30)
    if r.ok:
        js = r.json()
        arr = js.get("data") or []
        if arr:
            d = arr[0]
            mentions = d.get("social_volume", 0) or 0
            engagement = d.get("social_score", 0) or 0
            sentiment = (d.get("sentiment", 0) or 0) / 100 if isinstance(d.get("sentiment", 0), (int, float)) else 0.0
            influencer = bool((d.get("influencers") or 0) > 0 or (d.get("average_sentiment", 0) or 0) > 60)
            return {"mentions": mentions, "engagement": engagement, "sentiment": float(sentiment), "influencer": influencer}
    return {"mentions": 0, "engagement": 0, "sentiment": 0.0, "influencer": False}

def get_news_links(symbol: str, max_items: int = 2) -> List[str]:
    """Try CryptoPanic first, fallback to NewsAPI search."""
    links: List[str] = []
    if CRYPTOPANIC_KEY:
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {"auth_token": CRYPTOPANIC_KEY, "currencies": symbol.upper(), "filter": "rising", "public": "true"}
        r = SESSION.get(url, params=params, timeout=20)
        if r.ok:
            for p in r.json().get("results", [])[:max_items]:
                src = p.get("source", {}).get("url")
                if src: links.append(src)
    if len(links) < max_items and NEWSAPI_KEY:
        url = "https://newsapi.org/v2/everything"
        params = {"q": symbol.upper(), "pageSize": max_items - len(links), "sortBy": "publishedAt", "apiKey": NEWSAPI_KEY}
        r = SESSION.get(url, params=params, timeout=20)
        if r.ok:
            for a in r.json().get("articles", []):
                if a.get("url"): links.append(a["url"])
    return links[:max_items]

def tradingview_link(symbol: str) -> str:
    # Generic TradingView link; users can switch exchange in UI
    return f"https://www.tradingview.com/symbols/{symbol.upper()}{EXCHANGE_STABLE}/"
