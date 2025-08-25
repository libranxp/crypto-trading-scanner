# services/providers.py
import time
import math
import random
from typing import Dict, Any, List, Optional, Tuple
import httpx
from config import (
    COINMARKETCAP_API_KEY, POLYGON_API_KEY, LUNARCRUSH_API_KEY, SANTIMENT_API_KEY,
    NEWSAPI_KEY, CRYPTOPANIC_API_KEY, COINMARKETCAL_API_KEY, TWITTER_BEARER_TOKEN
)
import logging
logger = logging.getLogger(__name__)

def _client():
    return httpx.Client(timeout=15)

def _sleep_backoff(i: int):
    time.sleep(min(1.5*(i+1) + random.random(), 6))

# ---------- MARKET LIST & QUOTES ----------
def list_markets(limit: int = 300) -> List[Dict[str, Any]]:
    """
    Return list of {symbol, name, cmc_id} from CoinMarketCap.
    """
    if not COINMARKETCAP_API_KEY:
        return []
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"start": 1, "limit": limit, "convert": "USD", "sort": "market_cap"}
    for i in range(3):
        try:
            with _client() as c:
                res = c.get(url, headers=headers, params=params)
                if res.status_code == 429:
                    _sleep_backoff(i); continue
                res.raise_for_status()
                data = res.json()["data"]
                return [{"symbol": d["symbol"], "name": d["name"], "cmc_id": d["id"]} for d in data]
        except Exception as e:
            logger.warning("list_markets attempt %d failed: %s", i+1, e)
            _sleep_backoff(i)
    return []

def get_quote(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    CoinMarketCap quotes for symbols.
    """
    out = {}
    if not symbols or not COINMARKETCAP_API_KEY:
        return out
    sym_str = ",".join(symbols[:300])
    url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"symbol": sym_str, "convert": "USD"}
    for i in range(3):
        try:
            with _client() as c:
                res = c.get(url, headers=headers, params=params)
                if res.status_code == 429:
                    _sleep_backoff(i); continue
                res.raise_for_status()
                data = res.json()["data"]
                for sym, lst in data.items():
                    q = lst[0]["quote"]["USD"]
                    out[sym] = {
                        "price": q["price"],
                        "pct_change_24h": q["percent_change_24h"],
                        "market_cap": q.get("market_cap"),
                        "volume_24h": q.get("volume_24h")
                    }
                return out
        except Exception as e:
            logger.warning("get_quote attempt %d failed: %s", i+1, e)
            _sleep_backoff(i)
    return out

# ---------- OHLCV ----------
def get_ohlcv_polygon(symbol: str, limit: int = 300) -> Optional[Dict[str, List[float]]]:
    if not POLYGON_API_KEY:
        return None
    # Polygon Crypto aggregates (minute bars)
    url = f"https://api.polygon.io/v2/aggs/ticker/X:{symbol}USD/range/15/minute/now/now"
    params = {"adjusted":"true", "sort":"asc", "limit": limit, "apiKey": POLYGON_API_KEY}
    try:
        with _client() as c:
            r = c.get(url, params=params)
            if r.status_code == 429: return None
            r.raise_for_status()
            js = r.json()
            res = js.get("results") or []
            if not res: return None
            o = [x["o"] for x in res]; h=[x["h"] for x in res]; l=[x["l"] for x in res]; c=[x["c"] for x in res]; v=[x["v"] for x in res]
            return {"open": o, "high": h, "low": l, "close": c, "volume": v}
    except Exception as e:
        logger.warning("Polygon OHLCV failed for %s: %s", symbol, e)
        return None

# Fallback: Binance public klines (no key)
def get_ohlcv_binance(symbol: str, limit: int = 300, interval: str = "15m") -> Optional[Dict[str, List[float]]]:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": f"{symbol}USDT", "interval": interval, "limit": limit}
    try:
        with _client() as c:
            r = c.get(url, params=params)
            if r.status_code == 429: return None
            r.raise_for_status()
            data = r.json()
            if not data: return None
            o = [float(x[1]) for x in data]
            h = [float(x[2]) for x in data]
            l = [float(x[3]) for x in data]
            c_ = [float(x[4]) for x in data]
            v = [float(x[5]) for x in data]
            return {"open": o, "high": h, "low": l, "close": c_, "volume": v}
    except Exception as e:
        logger.warning("Binance OHLCV failed for %s: %s", symbol, e)
        return None

def get_ohlcv(symbol: str, limit: int = 300) -> Optional[Dict[str, List[float]]]:
    return get_ohlcv_polygon(symbol, limit) or get_ohlcv_binance(symbol, limit)

# ---------- SENTIMENT ----------
def get_lunarcrush(symbol: str) -> Dict[str, Any]:
    if not LUNARCRUSH_API_KEY: return {}
    url = "https://lunarcrush.com/api3/coins"
    params = {"symbol": symbol, "data_points": 1, "key": LUNARCRUSH_API_KEY}
    try:
        with _client() as c:
            r = c.get(url, params=params)
            if r.status_code == 429: return {}
            r.raise_for_status()
            d = r.json().get("data", [])
            if not d: return {}
            gc = d[0].get("galaxy_score")
            sv = d[0].get("social_volume")
            return {"galaxy_score": gc, "social_volume": sv}
    except Exception as e:
        logger.warning("LunarCrush failed %s", e); return {}

def get_santiment(symbol: str) -> Dict[str, Any]:
    # Minimal sentiment proxy (example endpoint requires token; returning stub if missing)
    if not SANTIMENT_API_KEY: return {}
    # Placeholder: you can wire Sanbase GraphQL here if needed
    return {}

def get_reddit(symbol: str) -> Dict[str, Any]:
    # Simple proxy via CryptoPanic search as sentiment-ish
    if not CRYPTOPANIC_API_KEY: return {}
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {"auth_token": CRYPTOPANIC_API_KEY, "currencies": symbol, "filter": "hot", "kind": "news"}
    try:
        with _client() as c:
            r = c.get(url, params=params)
            if r.status_code == 429: return {}
            r.raise_for_status()
            js = r.json()
            posts = js.get("results", [])
            return {"engagement": min(500, len(posts)*20)}  # crude engagement proxy
    except Exception as e:
        logger.warning("Reddit proxy failed: %s", e); return {}

def get_twitter(symbol: str) -> Dict[str, Any]:
    if not TWITTER_BEARER_TOKEN: return {}
    # Minimal counts via recent search (tweets per 15 min window)
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    params = {"query": f"({symbol}) (crypto OR coin) -is:retweet lang:en", "max_results": 10}
    try:
        with _client() as c:
            r = c.get(url, headers=headers, params=params)
            if r.status_code == 429: return {}
            r.raise_for_status()
            js = r.json()
            cnt = len(js.get("data", []))
            # influencer flag simplified (presence of verified users would require expansions)
            influencer_hit = cnt >= 10
            return {"mentions": cnt, "engagement": cnt*20, "influencer_hit": influencer_hit}
    except Exception as e:
        logger.warning("Twitter failed: %s", e); return {}

# ---------- NEWS / CATALYST ----------
def get_news(symbol: str) -> List[Dict[str, Any]]:
    out = []
    if NEWSAPI_KEY:
        url = "https://newsapi.org/v2/everything"
        params = {"q": f"{symbol} crypto", "sortBy": "publishedAt", "pageSize": 5, "apiKey": NEWSAPI_KEY, "language": "en"}
        try:
            with _client() as c:
                r = c.get(url, params=params)
                if r.status_code != 429:
                    r.raise_for_status()
                    for a in r.json().get("articles", []):
                        out.append({"source":"NewsAPI","title":a["title"],"url":a["url"],"ts":a.get("publishedAt"),"impact":1,"engagement":0})
        except Exception as e:
            logger.warning("NewsAPI failed: %s", e)

    if CRYPTOPANIC_API_KEY:
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {"auth_token": CRYPTOPANIC_API_KEY, "currencies": symbol, "filter": "hot", "kind": "news"}
        try:
            with _client() as c:
                r = c.get(url, params=params)
                if r.status_code != 429:
                    r.raise_for_status()
                    for p in r.json().get("results", []):
                        out.append({"source":"CryptoPanic","title":p.get("title"),"url":p.get("url"),"ts":p.get("published_at"),"impact":2,"engagement":(p.get('votes',{}) or {}).get('important',0)})
        except Exception as e:
            logger.warning("CryptoPanic failed: %s", e)

    if COINMARKETCAL_API_KEY:
        url = "https://developers.coinmarketcal.com/v1/events"
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        params = {"coins": symbol, "page": 1, "max": 3, "showOnly": "active"}
        try:
            with _client() as c:
                r = c.get(url, headers=headers, params=params)
                if r.status_code != 429:
                    r.raise_for_status()
                    for ev in r.json().get("body", []):
                        out.append({"source":"CoinMarketCal","title":ev.get("title"),"url":ev.get("source",{}).get("url") or ev.get("proof"),"ts":ev.get("date_event"),"impact":3,"engagement":0})
        except Exception as e:
            logger.warning("CMCcal failed: %s", e)

    return out
