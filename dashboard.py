# dashboard.py
from typing import List, Dict, Any
from fastapi import APIRouter
from config import TABLE_SCAN
from db import _supabase, supabase_enabled

router = APIRouter()

@router.get("/dashboard/json")
def dashboard_json() -> Dict[str, Any]:
    if not supabase_enabled():
        return {"items": [], "note": "Supabase disabled"}
    data = _supabase.table(TABLE_SCAN).select("*").order("timestamp", desc=True).limit(300).execute().data or []
    # de-dup by symbol, keep latest
    latest = {}
    for r in data:
        s = r["symbol"]
        if s not in latest:
            latest[s] = r
    items = list(latest.values())
    return {"items": items}

@router.get("/dashboard")
def dashboard_html():
    js = dashboard_json()
    items = js.get("items", [])
    # Minimal mobile-friendly table
    rows = []
    for it in items:
        badge = "🚀" if (it.get("sentiment_score") or 0) >= 0.7 else ("⚠️" if (it.get("rvol") or 1) >= 3 else "")
        rows.append(f"""
        <div class="card">
          <div class="line1">
            <span class="sym">{it.get('symbol')}</span>
            <span class="price">${it.get('price'):.6f}</span>
            <span class="chg">{it.get('pct_change_24h',0):+.2f}%</span>
            <span>{badge}</span>
          </div>
          <div class="line2">
            RSI {it.get('rsi') and round(it['rsi'],1)} • RVOL {it.get('rvol') and round(it['rvol'],2)} • Vol ${round((it.get('volume_24h') or 0)/1e6,2)}M
          </div>
          <div class="line3 small">
            EMA5>{'EMA13' if it.get('ema_aligned') else '…'} • VWAPΔ {it.get('vwap_delta_pct') and round(it['vwap_delta_pct'],2)}%
            • <a href="https://www.tradingview.com/symbols/{it.get('symbol')}USD/" target="_blank">TradingView</a>
          </div>
        </div>
        """)
    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 0; padding: 12px; }}
      .card {{ border:1px solid #eee; border-radius:12px; padding:12px; margin-bottom:10px; box-shadow: 0 1px 4px rgba(0,0,0,.04); }}
      .line1 {{ display:flex; gap:8px; align-items:center; justify-content:space-between; font-weight:600 }}
      .line2 {{ color:#444; margin-top:6px }}
      .line3 {{ color:#666; margin-top:6px }}
      .small {{ font-size: 12px; }}
      .sym {{ font-size:16px }}
      .price {{ font-weight:500 }}
      .chg {{ font-weight:600 }}
      a {{ color:#0a84ff; text-decoration:none }}
    </style></head>
    <body>
      <h2>Crypto Scanner Dashboard</h2>
      {''.join(rows) if rows else "<p>No items yet.</p>"}
    </body></html>
    """
    return html
