import os

# CoinGecko (no API key required)
COINGECKO_API_URL = os.environ.get("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Other optional APIs (if you want to wire them up later)
COINMARKETCAP_API_KEY = os.environ.get("COINMARKETCAP_API_KEY", "")
LUNARCRUSH_API_KEY = os.environ.get("LUNARCRUSH_API_KEY", "")

# Scanner config
DUPLICATE_ALERT_HOURS = int(os.environ.get("DUPLICATE_ALERT_HOURS", 6))
