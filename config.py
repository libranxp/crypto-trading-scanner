# config.py
import os
from datetime import timedelta

# --------- ENV ----------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY", "")
SANTIMENT_API_KEY = os.getenv("SANTIMENT_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")
COINMARKETCAL_API_KEY = os.getenv("COINMARKETCAL_API_KEY", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_SECRET = os.getenv("REDDIT_SECRET", "")

# --------- TABLES ----------
TABLE_SCAN = "crypto_scan_data"
TABLE_ALERTS = "crypto_alerts_log"

# --------- FILTERS (YOUR SPEC) ----------
FILTERS = {
    "price_min": 0.001,
    "price_max": 100.0,
    "vol_24h_min": 10_000_000,         # $10M
    "pct_change_min": 2.0,             # +2%
    "pct_change_max": 20.0,            # +20%
    "mcap_min": 10_000_000,            # $10M
    "mcap_max": 5_000_000_000,         # $5B
    "rsi_min": 50.0,
    "rsi_max": 70.0,
    "rvol_min": 2.0,                   # > 2x
    "ema_alignment": True,             # EMA5 > EMA13 > EMA50
    "vwap_proximity_pct": 2.0,         # ±2%
    "pump_reject_pct": 50.0,           # reject >50% in <1h
    "dup_suppression_hours": 6,
    "twitter_mentions_min": 10,
    "engagement_min": 100,
    "influencer_required": True,
    "sentiment_min": 0.6,
}

# --------- OPERATION ----------
TOP_N_TIER1 = 30           # number of Tier-1 candidates to store on dashboard
MAX_ALERTS_PER_SCAN = 5    # throttle to avoid Telegram spam
SCANNER_TIMEOUT_S = 25
CANDLES_LOOKBACK = 300     # data points for indicators
DASHBOARD_RETENTION_DAYS = 7

DUP_SUPPRESSION_DELTA = timedelta(hours=FILTERS["dup_suppression_hours"])

# Risk defaults
RISK = {
    "risk_per_trade_pct": 1.0,  # of equity
    "atr_sl_mult": 1.5,
    "atr_tp_mult": 2.5,
}
