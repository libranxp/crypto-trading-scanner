import requests
from config import (
    LUNARCRUSH_API_URL, LUNARCRUSH_API_KEY,
    REDDIT_API_URL, REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT,
    SANTIMENT_API_URL, SANTIMENT_API_KEY,
    TWITTER_API_URL, TWITTER_BEARER_TOKEN
)

def get_lunarcrush_sentiment(symbol):
    try:
        params = {"symbol": symbol.upper()}
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
        resp = requests.get(f"{LUNARCRUSH_API_URL}/assets", params=params, headers=headers)
        data = resp.json()
        if data["data"]:
            return data["data"][0].get("galaxy_score", 0)
    except Exception:
        pass
    return 0

def get_reddit_sentiment(subreddit="CryptoCurrency"):
    # Simple example: fetch top posts and analyze sentiment (placeholder)
    try:
        headers = {"User-Agent": REDDIT_USER_AGENT}
        url = f"{REDDIT_API_URL}/r/{subreddit}/hot.json?limit=10"
        resp = requests.get(url, headers=headers)
        posts = resp.json().get("data", {}).get("children", [])
        # Placeholder: return fixed sentiment score
        return 0.6
    except Exception:
        return 0

def get_santiment_sentiment(symbol):
    # Placeholder: GraphQL query to Santiment API (requires auth)
    # Return fixed demo value
    return 0.6

def get_twitter_metrics(symbol):
    # Placeholder: Use Twitter API v2 to get mentions and engagement
    # Return fixed demo values
    return {
        "mentions": 15,
        "engagement_score": 150,
        "influencer_flag": True
    }
