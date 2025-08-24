import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from datetime import datetime
from pathlib import Path

from scanner_tier1 import run_tier1
from scanner_tier2 import run_tier2
from scheduler import within_bst_window
from config import TIER1_CACHE_FILE, TIER2_CACHE_FILE

app = FastAPI(title="Crypto Trading Scanner", version="1.0.0")
scheduler = BackgroundScheduler(timezone=ZoneInfo("Europe/London"))

def _read_cache(path: Path):
    if not path.exists():
        return {"results": []}
    try:
        return json.loads(path.read_text() or "{}") or {"results": []}
    except Exception:
        return {"results": []}

def scheduled_job():
    if not within_bst_window():
        return
    # Tier 1 always; Tier 2 only if Tier 1 found results
    t1 = run_tier1()
    if t1:
        run_tier2()

@app.on_event("startup")
def startup_event():
    # Every 45 minutes during the day (we still gate by window inside the job)
    scheduler.add_job(scheduled_job, CronTrigger(minute="*/45"))
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# ---------- Public scan endpoints ----------
@app.get("/scan/auto")
def scan_auto():
    """Tier 1 on demand (kept to match your dashboard’s call)"""
    results = run_tier1()
    return {"results": results}

@app.post("/scan/tier2")
def scan_tier2():
    """Manual deep scan on latest Tier 1 cache + alerts"""
    results = run_tier2()
    return {"results": results}

# ---------- Result cache endpoints ----------
@app.get("/results/tier1")
def results_tier1():
    return _read_cache(TIER1_CACHE_FILE)

@app.get("/results/tier2")
def results_tier2():
    return _read_cache(TIER2_CACHE_FILE)
