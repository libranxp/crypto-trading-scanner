import os

# ----- Core service -----
PORT = int(os.getenv("PORT", "10000"))

# ----- External APIs (set these in Render env vars) -----
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY", "")
MESSARI_API_KEY = os.getenv("MESSARI_API_KEY", "")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")

# ----- Supabase -----
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# Storage behavior
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "scanner_results")

# Scanner filters (tweak via env without redeploy)
PRICE_MIN = float(os.getenv("PRICE_MIN", "0.01"))
PRICE_MAX = float(os.getenv("PRICE_MAX", "500"))
VOL_MIN   = float(os.getenv("VOL_MIN",   "1000000"))   # 1M
MCAP_MAX  = float(os.getenv("MCAP_MAX",  "2000000000")) # $2B
