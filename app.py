import os
import time
import requests
from fastapi import FastAPI
from typing import List, Dict

app = FastAPI()

# --- ENVIRONMENT VARIABLES ---
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CRYPTODESK_API_KEY = os.getenv("CRYPTODESK_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
TAPPI_API_KEY = os.getenv("TAPPI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

ALERT_HISTORY = {}  # symbol: last_alert_timestamp

# --- API FETCH FUNCTIONS ---

def fetch_coinmarketcap_coins() -> List[Dict]:
    """Fetch coins from CoinMarketCap (up to 500 for performance)."""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY}
    params = {"start": 1, "limit": 500, "convert": "USD"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        return []
    return resp.json().get("data", [])

def fetch_lunarcrush_social(symbol: str) -> Dict:
    url = f"https://api.lunarcrush.com/v2?data=assets&key={LUNARCRUSH_API_KEY}&symbol={symbol}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return {}
    data = resp.json().get("data", [{}])[0]
    return {
        "twitter_mentions": data.get("twitter_mentions", 0),
        "engagement_score": data.get("galaxy_score", 0),
        "influencer_flag": data.get("influencer_score", 0) > 0,
        "sentiment_score": data.get("alt_rank", 0) / 100 if data.get("alt_rank") else 0
    }

def fetch_messari_metrics(symbol: str) -> Dict:
    url = f"https://data.messari.io/api/v1/assets/{symbol.lower()}/metrics"
    headers = {"x-messari-api-key": MESSARI_API_KEY}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {}
    data = resp.json().get("data", {})
    return {
        "rvol": data.get("market_data", {}).get("real_volume_last_24_hours", 0),
        "marketcap": data.get("marketcap", {}).get("current_marketcap_usd", 0)
    }

def fetch_cryptopanic_news(symbol: str) -> int:
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&currencies={symbol.lower()}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return 0
    return len(resp.json().get("results", []))

def fetch_newsapi_mentions(symbol: str) -> int:
    url = f"https://newsapi.org/v2/everything"
    params = {"q": symbol, "apiKey": NEWSAPI_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return 0
    return resp.json().get("totalResults", 0)

def fetch_twitter_mentions(symbol: str) -> int:
    url = f"https://api.twitter.com/2/tweets/search/recent?query={symbol}&max_results=100"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return 0
    return len(resp.json().get("data", []))

def fetch_reddit_mentions(symbol: str) -> int:
    # For simplicity, just count posts in r/CryptoCurrency mentioning the symbol
    url = f"https://www.reddit.com/r/CryptoCurrency/search.json?q={symbol}&restrict_sr=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return 0
    return len(resp.json().get("data", {}).get("children", []))

def fetch_santiment_sentiment(symbol: str) -> float:
    url = f"https://api.santiment.net/graphql"
    headers = {"Authorization": f"Apikey {SANTIMENT_API_KEY}"}
    query = {
        "query": """
        {
          sentiment(
            slug: "%s"
            from: "%s"
            to: "%s"
            interval: "1d"
          ) {
            positiveScore
            negativeScore
          }
        }
        """ % (symbol.lower(), time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)), time.strftime("%Y-%m-%d", time.gmtime()))
    }
    resp = requests.post(url, headers=headers, json=query)
    if resp.status_code != 200:
        return 0
    data = resp.json().get("data", {}).get("sentiment", [])
    if not data:
        return 0
    pos = data[-1].get("positiveScore", 0)
    neg = data[-1].get("negativeScore", 0)
    return pos / (pos + neg) if (pos + neg) > 0 else 0

# --- INDICATOR CALCULATIONS ---

def calculate_indicators(coin: Dict) -> Dict:
    # Example: Use CoinMarketCap historical data for indicators if available
    # For simplicity, only EMA alignment and RSI are calculated here
    prices = coin.get("quote", {}).get("USD", {}).get("sparkline", [])
    if not prices or len(prices) < 50:
        return {}

    # RSI calculation (14-period simplified)
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d for d in deltas[-14:] if d > 0]
    losses = [-d for d in deltas[-14:] if d < 0]
    avg_gain = sum(gains)/14 if gains else 0.0001
    avg_loss = sum(losses)/14 if losses else 0.0001
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # EMA calculation helper
    def ema(prices_list, period):
        k = 2 / (period + 1)
        ema_val = prices_list[0]
        for price in prices_list[1:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val

    ema5 = ema(prices[-20:], 5)
    ema13 = ema(prices[-50:], 13)
    ema50 = ema(prices, 50)
    ema_alignment = ema5 > ema13 > ema50

    # VWAP proximity (approximate)
    vwap = sum(prices[-20:]) / len(prices[-20:])
    vwap_proximity = abs(coin["quote"]["USD"]["price"] - vwap) / vwap <= 0.02

    # RVOL: relative volume (24h volume / average daily volume over 7 days)
    avg_vol = coin["quote"]["USD"]["volume_24h"] / 7 if coin["quote"]["USD"]["volume_24h"] else 0.0001
    rvol = coin["quote"]["USD"]["volume_24h"] / avg_vol if avg_vol else 0

    # Pump filter: reject if >50% spike in last hour (approx 12 data points in sparkline per hour)
    if len(prices) > 12:
        last_hour = prices[-12:]
        pump_filter = (max(last_hour) - min(last_hour)) / min(last_hour) > 0.5
    else:
        pump_filter = False

    return {
        "rsi": rsi,
        "ema_alignment": ema_alignment,
        "vwap_proximity": vwap_proximity,
        "rvol": rvol,
        "pump_filter": pump_filter
    }

# --- FILTERS ---

def passes_filters(coin: Dict, indicators: Dict, social: Dict, sentiment: float, news_mentions: int, twitter_mentions: int, reddit_mentions: int) -> bool:
    price = coin["quote"]["USD"]["price"]
    volume = coin["quote"]["USD"]["volume_24h"]
    market_cap = coin["quote"]["USD"]["market_cap"]
    price_change = coin["quote"]["USD"].get("percent_change_24h", 0)
    symbol = coin["symbol"]

    if not (0.001 <= price <= 100):
        return False
    if volume < 10_000_000:
        return False
    if not (2 <= price_change <= 20):
        return False
    if not (10_000_000 <= market_cap <= 5_000_000_000):
        return False
    if not (50 <= indicators.get("rsi", 0) <= 70):
        return False
    if indicators.get("rvol", 0) < 2:
        return False
    if not indicators.get("ema_alignment", False):
        return False
    if not indicators.get("vwap_proximity", False):
        return False
    if indicators.get("pump_filter", False):
        return False
    if ALERT_HISTORY.get(symbol, 0) > time.time() - 6*3600:
        return False
    if social.get("twitter_mentions", 0) + twitter_mentions < 10:
        return False
    if social.get("engagement_score", 0) < 100:
        return False
    if not social.get("influencer_flag", False):
        return False
    if sentiment < 0.6:
        return False
    if news_mentions + reddit_mentions < 10:
        return False
    return True

# --- TELEGRAM ALERT ---

def send_telegram_alert(coin: Dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    msg = (
        f"🚨 *{coin['name']}* ({coin['symbol']})\n"
        f"Price: ${coin['quote']['USD']['price']:.4f}\n"
        f"Volume: ${coin['quote']['USD']['volume_24h']:,}\n"
        f"Market Cap: ${coin['quote']['USD']['market_cap']:,}\n"
        f"24h Change: {coin['quote']['USD'].get('percent_change_24h', 0):.2f}%\n"
        f"https://coinmarketcap.com/currencies/{coin['slug']}/"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

# --- MAIN ENDPOINT ---

@app.get("/scan/auto")
def scan_auto():
    coins = fetch_coinmarketcap_coins()
    results = []
    for coin in coins:
        symbol = coin["symbol"]
        indicators = calculate_indicators(coin)
        if not indicators:
            continue
        social = fetch_lunarcrush_social(symbol)
        sentiment = fetch_santiment_sentiment(symbol)
        news_mentions = fetch_newsapi_mentions(symbol)
        twitter_mentions = fetch_twitter_mentions(symbol)
        reddit_mentions = fetch_reddit_mentions(symbol)
        if passes_filters(coin, indicators, social, sentiment, news_mentions, twitter_mentions, reddit_mentions):
            results.append({
                "symbol": symbol,
                "name": coin["name"],
                "price": coin["quote"]["USD"]["price"],
                "market_cap": coin["quote"]["USD"]["market_cap"],
                "volume": coin["quote"]["USD"]["volume_24h"],
                "price_change_24h": coin["quote"]["USD"].get("percent_change_24h", 0),
                "rsi": indicators.get("rsi"),
                "rvol": indicators.get("rvol"),
                "ema_alignment": indicators.get("ema_alignment"),
                "vwap_proximity": indicators.get("vwap_proximity"),
                "twitter_mentions": social.get("twitter_mentions"),
                "engagement_score": social.get("engagement_score"),
                "influencer_flag": social.get("influencer_flag"),
                "sentiment_score": sentiment,
                "news_mentions": news_mentions,
                "reddit_mentions": reddit_mentions,
                "coinmarketcap_url": f"https://coinmarketcap.com/currencies/{coin['slug']}/"
            })
            if ALERT_HISTORY.get(symbol, 0) < time.time() - 6*3600:
                send_telegram_alert(coin)
                ALERT_HISTORY[symbol] = time.time()
    return {"results": results}
