# app.py
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from services.scanner import run_auto_scan, run_manual_scan, scan_and_alert
from dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Crypto Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/scan/auto")
def scan_auto():
    res = run_auto_scan()
    return {"count": len(res), "items": res}

@app.get("/scan/manual")
def scan_manual(symbols: List[str] = Query(default=[])):
    res = run_manual_scan(symbols)
    return {"count": len(res), "items": res}

@app.post("/scan/alert")
def scan_alert():
    res = scan_and_alert()
    return {"count": len(res)}

app.include_router(dashboard_router)
