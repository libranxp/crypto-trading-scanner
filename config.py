import os

MAX_MARKETS_TO_SCAN = int(os.getenv("MAX_MARKETS_TO_SCAN", "200"))
MAX_TIER2_DEEP_CANDLES = int(os.getenv("MAX_TIER2_DEEP_CANDLES", "250"))
QUOTE_CCY = os.getenv("EXCHANGE_STABLE", "USD").upper()

# Tier 1 / coarse filters (applied via CMC metadata only)
PRICE_MIN = 0.001
PRICE_MAX = 100.0
VOL_MIN = 10_000_000           # 24h USD volume
MCAP_MIN = 10_000_000
MCAP_MAX = 5_000_000_000
CHANGE_MIN_PCT = 2.0
CHANGE_MAX_PCT = 20.0

# Tier 2 / technical + sentiment thresholds
RSI_MIN = 50.0
RSI_MAX = 70.0
RVOL_MIN = 2.0
VWAP_PROX_PCT = 2.0           # within ±2%
SOCIAL_MENTIONS_MIN = 10
ENGAGEMENT_MIN = 100
SENTIMENT_MIN = 0.6
REJECT_PUMP_PCT = 50.0        # reject >50% spike in <1h
