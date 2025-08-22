from fastapi import FastAPI, Query
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_scan
from scheduler import manual_scan

app = FastAPI()

@app.get("/")
def health():
    return {"status": "Crypto Scanner running"}

@app.get("/scan/auto")
def auto_scan():
    results = tier1_scan()
    return {"tier": 1, "results": results}

@app.get("/scan/manual")
def manual(symbols: str = Query(..., description="Comma-separated symbols")):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = manual_scan(symbol_list)
    return {"tier": 2, "results": results}

@app.get("/scan/event")
def event_scan(symbol: str):
    results = manual_scan([symbol])
    return {"tier": 2, "results": results}
