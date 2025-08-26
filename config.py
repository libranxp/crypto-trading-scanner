# config.py
import os

# Dashboard / telegram config (dashboard only uses supabase)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DASHBOARD_PORT = int(os.getenv("PORT", "10000"))
# Optional: the dashboard can show a link back to TradingView or other templates
TRADINGVIEW_BASE = os.getenv("TRADINGVIEW_BASE", "https://www.tradingview.com/symbols")
