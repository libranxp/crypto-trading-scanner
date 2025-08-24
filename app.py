import logging
from typing import Optional
from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from services.scanner import run_auto_scan
from db import supabase, TABLE
from config import PORT

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Crypto Trading Scanner", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def home():
    return {
        "service": "crypto-trading-scanner",
        "status": "ok",
        "endpoints": ["/scan/auto", "/scan/manual?symbols=BTC,ETH", "/healthz"]
    }

# Render’s health checks sometimes use HEAD; return 200 to avoid 405 logs.
@app.head("/")
def head_root():
    return Response(status_code=200)

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/scan/auto")
def scan_auto():
    try:
        results = run_auto_scan()
        return {"status": "success", "count": len(results), "results": results}
    except Exception as e:
        logging.exception("❌ Auto scan failed")
        return {"status": "error", "message": str(e)}

@app.get("/scan/manual")
def scan_manual(symbols: Optional[str] = Query(None, description="Comma-separated symbols")):
    """
    Manual fetch reads from Supabase latest rows that match provided symbols.
    No hardcoded defaults: if no symbols given -> returns empty set.
    """
    if not symbols:
        return {"status": "success", "count": 0, "results": []}

    wanted = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not wanted:
        return {"status": "success", "count": 0, "results": []}

    try:
        # Get most recent 200 and filter in-memory to keep it simple & cheap
        resp = supabase.table(TABLE).select("*").order("id", desc=True).limit(200).execute()
        rows = resp.data or []
        out = [r for r in rows if str(r.get("symbol", "")).upper() in wanted]
        return {"status": "success", "count": len(out), "results": out}
    except Exception as e:
        logging.error(f"❌ Manual scan failed: {e}")
        return {"status": "error", "message": str(e)}

# If you ever run locally: `python app.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
