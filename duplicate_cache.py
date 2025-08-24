import time
from typing import Dict

# In-memory cache of alerted symbols -> timestamp
_alert_cache: Dict[str, float] = {}

def should_alert(symbol: str, cooldown_hours: int) -> bool:
    """
    Return True if we should alert for this symbol; otherwise False.
    Updates the cache when returning True.
    """
    now = time.time()
    ts = _alert_cache.get(symbol)
    if ts and (now - ts) < cooldown_hours * 3600:
        return False
    _alert_cache[symbol] = now
    return True
