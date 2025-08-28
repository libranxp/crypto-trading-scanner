# app.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from db import supabase, TABLE
import logging
import json
from datetime import datetime

app = FastAPI()

def get_rows_from_supabase(limit=200):
    if not supabase:
        return []
    try:
        res = supabase.table(TABLE).select("*").order("ai_score", {"ascending": False}).limit(limit).execute()
        data = res.data if hasattr(res, "data") else res
        return data or []
    except Exception:
        logging.exception("Supabase fetch failed")
        return []

def get_rows_local():
    path = "tier2_results.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

@app.get("/health")
def health():
    return JSONResponse({"status": "running", "time": datetime.utcnow().isoformat()})

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    # prefer Supabase
    rows = get_rows_from_supabase() or get_rows_local()

    # Build a simple responsive HTML table
    html = """
    <!doctype html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>Crypto Scanner Dashboard</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 12px; background:#f7f9fb; color:#0b1220; }
        .card { background:#fff; border-radius:8px; padding:12px; margin-bottom:10px; box-shadow:0 1px 4px rgba(0,0,0,0.06);}
        table{border-collapse:collapse;width:100%}
        th,td{padding:8px;text-align:left;border-bottom:1px solid #eee;font-size:13px}
        th{background:#fafafa;position:sticky;top:0}
        @media (max-width:600px){
          .desktop-only{display:none}
        }
        .badge{display:inline-block;padding:4px 8px;border-radius:12px;font-weight:600;background:#eef9f0;color:#1b7f3a}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>Crypto Scanner Dashboard</h2>
        <p>Showing latest signals. Refresh to update.</p>
      </div>
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th class="desktop-only">Price</th>
              <th>AI Score</th>
              <th class="desktop-only">RSI</th>
              <th class="desktop-only">EMA (5/13/50)</th>
              <th>RVOL</th>
              <th class="desktop-only">ATR</th>
              <th>Risk (SL/TP)</th>
            </tr>
          </thead>
          <tbody>
    """

    for r in rows:
        ticker = (r.get("ticker") or r.get("coin_id") or "").upper()
        price = r.get("price", "")
        ai = r.get("ai_score", "")
        rsi = r.get("rsi", "")
        ema5 = r.get("ema5", "")
        ema13 = r.get("ema13", "")
        ema50 = r.get("ema50", "")
        rvol = r.get("rvol", "")
        atr = r.get("atr", "")
        risk = r.get("risk", {})
        sl = (risk.get("stop_loss") if isinstance(risk, dict) else "")
        tp = (risk.get("take_profit") if isinstance(risk, dict) else "")

        html += f"""
            <tr>
              <td><strong>{ticker}</strong><div style="font-size:11px;color:#666">{r.get("name","")}</div></td>
              <td class="desktop-only">{price}</td>
              <td><span class="badge">{ai}</span></td>
              <td class="desktop-only">{rsi}</td>
              <td class="desktop-only">{ema5 or ''}/{ema13 or ''}/{ema50 or ''}</td>
              <td>{rvol}</td>
              <td class="desktop-only">{atr}</td>
              <td>SL: {round(sl,6) if isinstance(sl,(float,int)) else sl}<br/>TP: {round(tp,6) if isinstance(tp,(float,int)) else tp}</td>
            </tr>
        """

    html += """
          </tbody>
        </table>
      </div>
      <div style="text-align:center;color:#888;font-size:12px">Updated: {time}</div>
    </body>
    </html>
    """.format(time=datetime.utcnow().isoformat())

    return HTMLResponse(content=html)
