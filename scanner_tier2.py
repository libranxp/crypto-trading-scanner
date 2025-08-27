import argparse
from technical_indicators import compute_metrics
from sentiment_analysis import compute_sentiment
from catalyst_analysis import fetch_catalysts
from telegram_alerts import send_alert
from db import supabase   # ✅ now works correctly
