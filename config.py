import os
from pathlib import Path

# Core data dir (persist within container lifecycle)
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# External APIs
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Optional APIs (only used if keys exist)
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Scheduler window (BST)
SCHEDULE_START_HOUR = int(os.getenv("SCHEDULE_START_HOUR_BST", "8"))   # 08:00 BST
SCHEDULE_END_HOUR   = int(os.getenv("SCHEDULE_END_HOUR_BST", "21"))    # 21:00 BST
SCHEDULE_INTERVAL_MIN = int(os.getenv("SCHEDULE_INTERVAL_MIN", "45"))  # every 45 min

# Files for caching and duplicate control
ALERTS_LOG_FILE = DATA_DIR / "alerts_log.json"
TIER1_CACHE_FILE = DATA_DIR / "tier1_latest.json"
TIER2_CACHE_FILE = DATA_DIR / "tier2_latest.json"
