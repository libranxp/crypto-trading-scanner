import time
from typing import Dict

# In-memory cache during a single run (GA job). For multi-run dedupe, back it with Supabase later.
_seen: Dict[str, float] = {}
WINDOW_SEC = 6 * 60 * 60  # 6 hours

def seen_recent(symbol: str) -> bool:
    now = time.time()
    t = _seen.get(symbol.upper())
    return (t is not None) and (now - t < WINDOW_SEC)

def mark_seen(symbol: str):
    _seen[symbol.upper()] = time.time()
