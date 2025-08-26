from fastapi import FastAPI
from services.scanner import run_auto_scan, scan_and_alert  # ✅ removed run_manual_scan

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/scan")
def manual_scan():
    """Trigger a manual scan via API"""
    return scan_and_alert()

@app.get("/auto-scan")
def auto_scan():
    """Trigger automated scan (used by GitHub Actions/cronjob)"""
    return run_auto_scan()
