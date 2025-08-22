import requests
from config import (
    COINMARKETCAL_API_URL, COINMARKETCAL_API_KEY,
    NEWSAPI_URL, NEWSAPI_KEY,
    CRYPTOPANIC_API_URL, CRYPTOPANIC_API_KEY,
    MESSARI_API_URL, MESSARI_API_KEY
)

def get_coinmarketcal_events(symbol):
    try:
        headers = {"x-api-key": COINMARKETCAL_API_KEY}
        params = {"coins": symbol.lower()}
        resp = requests.get(f"{COINMARKETCAL_API_URL}/events", headers=headers, params=params)
        data = resp.json()
        return data.get("body", [])
    except Exception:
        return []

def get_newsapi_news(query):
    try:
        params = {"q": query, "apiKey": NEWSAPI_KEY, "language": "en", "pageSize": 5}
        resp = requests.get(f"{NEWSAPI_URL}/everything", params=params)
        data = resp.json()
        return data.get("articles", [])
    except Exception:
        return []

def get_cryptopanic_news():
    try:
        params = {"auth_token": CRYPTOPANIC_API_KEY}
        resp = requests.get(CRYPTOPANIC_API_URL, params=params)
        data = resp.json()
        return data.get("results", [])
    except Exception:
        return []

def get_messari_news(symbol):
    try:
        resp = requests.get(f"{MESSARI_API_URL}/assets/{symbol}/news", headers={"x-messari-api-key": MESSARI_API_KEY})
        data = resp.json()
        return data.get("data", [])
    except Exception:
        return []
