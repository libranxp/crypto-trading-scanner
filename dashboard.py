# dashboard.py
import math
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
from db import get_supabase, TABLE
from config import TRADINGVIEW_BASE
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="Crypto Scanner Dashboard", docs_url="/docs")

def format_money(x):
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return str(x or "")

def risk_color(risk_text: str) -> str:
    st = (risk_text or "").lower()
    if "low" in st:
        return "#d4f7d4"  # light green
    if "high" in st:
        return "#ffd6d6"  # light red
    return "#fff4cc"  # light yellow for medium/unknown

def build_tradingview_link(symbol: str) -> str:
    # Basic conversion - user may want to customize exchange prefix
    return f"{TRADINGVIEW_BASE}/{symbol}"

@app.get("/api/data")
async def api_data(limit: int = 200):
    """
    Return JSON of latest scanner rows from Supabase.
    limit param caps results (default 200).
    """
    try:
        supabase = get_supabase()
        # select commonly expected fields; fallback to '*' if your table has different schema
        q = supabase.table(TABLE).select("*").order("updated_at", desc=True).limit(limit)
        res = q.execute()
        if res.error:
            logger.error("Supabase fetch error: %s", res.error)
            return JSONResponse({"error": str(res.error)}, status_code=500)
        rows = res.data or []
        # ensure expected fields exist and convert types lightly
        for r in rows:
            r["price_display"] = format_money(r.get("price"))
            r["ai_score_display"] = f"{r.get('ai_score', '')}" if r.get("ai_score") is not None else ""
            r["updated_at_display"] = r.get("updated_at") or r.get("created_at") or ""
            # direct tradingview link if not present
            if not r.get("tradingview_link") and r.get("symbol"):
                r["tradingview_link"] = build_tradingview_link(r["symbol"])
        return JSONResponse(rows)
    except Exception as e:
        logger.exception("Error in /api/data: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Returns a mobile-friendly dashboard page that pulls /api/data via JS.
    """
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Crypto Scanner Dashboard</title>
      <style>
        body{font-family:Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin:0; padding:0; background:#f7f8fb; color:#0f172a}
        header{background:#0b1220;color:white;padding:12px 16px}
        header h1{margin:0;font-size:18px}
        .container{padding:12px}
        .controls{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
        .refresh{background:#0b1220;color:#fff;padding:8px 12px;border-radius:8px;border:none;cursor:pointer}
        .table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(2,6,23,0.06)}
        th,td{padding:10px 12px;text-align:left;font-size:13px;border-bottom:1px solid #f1f5f9}
        th{background:#fbfdff;position:sticky;top:0;z-index:2}
        .symbol{font-weight:700}
        .badge{padding:6px 8px;border-radius:8px;font-size:12px;display:inline-block}
        .mini{font-size:11px;color:#475569}
        @media (max-width:800px){
          th:nth-child(n+6), td:nth-child(n+6){display:none}
        }
      </style>
    </head>
    <body>
      <header>
        <h1>Crypto Scanner Dashboard</h1>
      </header>
      <div class="container">
        <div class="controls">
          <button class="refresh" onclick="loadData()">🔄 Refresh</button>
          <div class="mini">Auto-updates every 60s</div>
        </div>

        <div id="tableWrap">
          <table class="table" id="resultsTable">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>Change %</th>
                <th>RSI</th>
                <th>EMA</th>
                <th>VWAP</th>
                <th>ATR</th>
                <th>RVOL</th>
                <th>Volume</th>
                <th>AI Score</th>
                <th>Risk</th>
                <th>Links</th>
              </tr>
            </thead>
            <tbody id="resultsBody">
              <tr><td colspan="12" class="mini">Loading…</td></tr>
            </tbody>
          </table>
        </div>

      </div>

      <script>
        async function loadData(){
          const tbody = document.getElementById('resultsBody');
          tbody.innerHTML = '<tr><td colspan="12" class="mini">Loading…</td></tr>';
          try {
            const res = await fetch('/api/data?limit=200');
            const data = await res.json();
            if (data.error) { tbody.innerHTML = '<tr><td colspan="12">Error: '+data.error+'</td></tr>'; return; }
            if (!Array.isArray(data) || data.length === 0){
              tbody.innerHTML = '<tr><td colspan="12" class="mini">No rows in scanner_results</td></tr>';
              return;
            }
            // build rows
            tbody.innerHTML = '';
            for (const r of data){
              const symbol = r.symbol || '';
              const price = r.price_display || r.price || '';
              const change = r.price_change_percent ? (Number(r.price_change_percent).toFixed(2)+'%') : (r.change_pct ? r.change_pct : '');
              const rsi = r.rsi || '';
              const ema = r.ema_signal || '';
              const vwap = r.vwap || '';
              const atr = r.atr || '';
              const rvol = r.rvol || '';
              const vol = r.volume ? Number(r.volume).toLocaleString() : '';
              const ai = r.ai_score_display || '';
              const risk = r.risk || '';
              const links = [];
              if (r.tradingview_link) links.push(`<a href="${r.tradingview_link}" target="_blank">TV</a>`);
              if (r.news_link) links.push(`<a href="${r.news_link}" target="_blank">News</a>`);
              if (r.sentiment_link) links.push(`<a href="${r.sentiment_link}" target="_blank">Sentiment</a>`);
              if (r.catalyst_link) links.push(`<a href="${r.catalyst_link}" target="_blank">Catalyst</a>`);
              const row = document.createElement('tr');
              row.innerHTML = `
                <td class="symbol">${symbol}</td>
                <td>${price}</td>
                <td>${change}</td>
                <td>${rsi}</td>
                <td>${ema}</td>
                <td>${vwap}</td>
                <td>${atr}</td>
                <td>${rvol}</td>
                <td>${vol}</td>
                <td>${ai}</td>
                <td style="background:${getRiskColor(risk)}">${risk}</td>
                <td>${links.join(' • ')}</td>
              `;
              tbody.appendChild(row);
            }
          } catch (e) {
            tbody.innerHTML = '<tr><td colspan="12">Fetch error: '+e.toString()+'</td></tr>';
          }
        }

        function getRiskColor(r){
          const s = (r||'').toLowerCase();
          if (s.includes('low')) return '#d4f7d4';
          if (s.includes('high')) return '#ffd6d6';
          return '#fff4cc';
        }

        // auto refresh every 60 seconds
        loadData();
        setInterval(loadData, 60000);
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
