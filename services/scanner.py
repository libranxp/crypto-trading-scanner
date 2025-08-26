import pandas as pd
import requests

def run_auto_scan():
    """
    Run automatic scan (used by scheduler / GitHub Actions / Render cronjob)
    """
    # ✅ Replace this with your real scanning logic
    return {"message": "Auto scan completed successfully"}

def scan_and_alert():
    """
    Run manual scan + send alerts
    """
    # ✅ Replace this with your real alert logic (Telegram, Supabase, etc.)
    return {"message": "Manual scan & alert triggered successfully"}
