import logging
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_analysis_for_coin
from scheduler import start_scheduler, stop_scheduler
from typing import List, Optional
import uvicorn

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Crypto Trading Scanner API")

@app.on_event("startup")
def on_startup():
    logger.info("Starting scheduler...")
    try:
        start_scheduler()
    except Exception:
        logger.exception("Failed to start scheduler")

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down scheduler...")
    try:
        stop_scheduler()
    except Exception:
        logger.exception("Failed to stop scheduler")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Crypto Scanner API running"}

@app.get("/scan/auto")
async def scan_auto():
    """
    Tier1 auto scan: runs lightweight filters and returns results list.
    """
    try:
        results = tier1_scan(limit_coins=250)
        # ensure list of dicts
        sanitized = []
        for r in results:
            if not isinstance(r, dict):
                logger.warning("scan_auto skipping invalid item: %s", r)
                continue
            # minimal sanitization
            sanitized.append(r)
        return JSONResponse({"results": sanitized})
    except Exception as e:
        logger.exception("Auto scan failed: %s", e)
        return JSONResponse({"error": "Auto scan failed", "details": str(e)}, status_code=500)

@app.get("/scan/manual")
async def scan_manual(symbols: Optional[str] = Query(None, description="Comma separated symbols, or leave blank for sample")):
    """
    Tier2 manual scan: accept comma separated symbols (e.g. BTC,ETH).
    If no symbols provided, returns a small sample list (safe).
    """
    try:
        out = []
        if symbols:
            symbols_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
            # map symbols to CoinGecko ids is non-trivial; for demo we will try to match by name fetch
            # Better approach: call Tier1 and filter by symbol.
            candidates = tier1_scan(limit_coins=500)
            sym_to_info = {c.get("symbol", "").upper(): c for c in candidates if isinstance(c, dict)}
            for s in symbols_list:
                info = sym_to_info.get(s)
                if info:
                    enriched = tier2_analysis_for_coin(info)
                    out.append(enriched)
                else:
                    out.append({"symbol": s, "error": "Not found in latest markets scan"})
        else:
            # no symbols — return empty array (don't preseed tickers)
            out = []
        return JSONResponse({"results": out})
    except Exception as e:
        logger.exception("Manual scan failed: %s", e)
        return JSONResponse({"error": "Manual scan failed", "details": str(e)}, status_code=500)

# if you want to run locally with `python app.py`
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000, log_level="info")
