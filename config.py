import os

# API URLs
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINMARKETCAP_API_URL = "https://pro-api.coinmarketcap.com/v1"
COINMARKETCAL_API_URL = "https://developers.coinmarketcal.com/v1"
LUNARCRUSH_API_URL = "https://api.lunarcrush.com/v2"
ALPHAVANTAGE_API_URL = "https://www.alphavantage.co/query"
REDDIT_API_URL = "https://www.reddit.com"
SANTIMENT_API_URL = "https://api.santiment.net/graphql"
MESSARI_API_URL = "https://data.messari.io/api/v1"
TWITTER_API_URL = "https://api.twitter.com/2"
NEWSAPI_URL = "https://newsapi.org/v2"
POLYGON_API_URL = "https://api.polygon.io"
CRYPTODESK_API_URL = "https://api.cryptodesk.com"
CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1"
TAPPI_API_URL = "https://api.tappi.io"

# API Keys (set these in your environment variables)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  # Optional for CoinGecko
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
CRYPTODESK_API_KEY = os.getenv("CRYPTODESK_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
TAPPI_API_KEY = os.getenv("TAPPI_API_KEY")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
