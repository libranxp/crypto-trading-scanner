# duplicate_cache.py
import time
from typing import Dict, Tuple
from config import DUP_SUPPRESSION_DELTA
from db import get_recent_alerts

# Simple in-proc memory
_last_alerts: Dict[str, int] = {}

def should_suppress(symbol: str) -> bool:
    now = int(time.time())
    last = _last_alerts.get(symbol)
    if last and now - last < DUP_SUPPRESSION_DELTA.total_seconds():
        return True
    # Check DB for last 6h
    recent = get_recent_alerts(symbol=symbol, since_unix=now - int(DUP_SUPPRESSION_DELTA.total_seconds()))
    if recent:
        _last_alerts[symbol] = recent[0]["ts"]
        return True
    return False

def mark_alert(symbol: str):
    _last_alerts[symbol] = int(time.time())
