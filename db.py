# db.py
import os
import time
from typing import Any, Dict, List, Optional
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, TABLE_SCAN, TABLE_ALERTS
import logging

logger = logging.getLogger(__name__)

_supabase = None
try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        from supabase import create_client, Client
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("✅ Supabase client initialized.")
    else:
        logger.warning("⚠️ Supabase credentials missing; DB writes disabled.")
except Exception as e:
    logger.exception("Supabase init failed: %s", e)

def supabase_enabled() -> bool:
    return _supabase is not None

def upsert_scan_rows(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    if not supabase_enabled():
        logger.debug("[DB SKIP] upsert_scan_rows len=%d", len(rows))
        return
    _supabase.table(TABLE_SCAN).upsert(rows, on_conflict="symbol,timestamp").execute()

def log_alert(symbol: str, payload: Dict[str, Any]) -> None:
    if not supabase_enabled():
        logger.debug("[DB SKIP] log_alert %s", symbol)
        return
    rec = {"symbol": symbol, "payload": payload, "ts": int(time.time())}
    _supabase.table(TABLE_ALERTS).insert(rec).execute()

def get_recent_alerts(symbol: Optional[str]=None, since_unix: Optional[int]=None) -> List[Dict[str, Any]]:
    if not supabase_enabled():
        return []
    q = _supabase.table(TABLE_ALERTS).select("*")
    if symbol:
        q = q.eq("symbol", symbol)
    if since_unix:
        q = q.gte("ts", since_unix)
    res = q.order("ts", desc=True).limit(1000).execute()
    return res.data or []
