import logging
from typing import Any, Dict, List, Union
import requests
from config import COINMARKETCAP_API_KEY, LUNARCRUSH_API_KEY, MESSARI_API_KEY

Json = Union[Dict[str, Any], List[Any]]

def _safe_get_json(resp: requests.Response) -> Json:
    try:
        return resp.json()
    except Exception as e:
        logging.error(f"❌ Failed to decode JSON: {e}")
        return {}

def fetch_cmc(limit: int = 200) -> List[Dict[str, Any]]:
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY} if COINMARKETCAP_API_KEY else {}
    try:
        r = requests.get(url, headers=headers, params={"limit": limit, "convert": "USD"}, timeout=30)
        r.raise_for_status()
        data = _safe_get_json(r)
        # CMC payload has top-level keys: status (dict) and data (list). Guard types carefully.
        items = data.get("data", []) if isinstance(data, dict) else []
        return items if isinstance(items, list) else []
    except Exception as e:
        logging.error(f"❌ CMC fetch failed: {e}")
        return []

def fetch_lunarcrush() -> List[Dict[str, Any]]:
    if not LUNARCRUSH_API_KEY:
        return []
    url = f"https://lunarcrush.com/api3/coins?data=market&key={LUNARCRUSH_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = _safe_get_json(r)
        items = data.get("data", []) if isinstance(data, dict) else []
        return items if isinstance(items, list) else []
    except Exception as e:
        logging.error(f"❌ LunarCrush fetch failed: {e}")
        return []

def fetch_messari(page_size: int = 200) -> List[Dict[str, Any]]:
    # Public Messari endpoints don’t always require a key, but we still guard.
    url = "https://data.messari.io/api/v2/assets"
    try:
        r = requests.get(url, params={"page": 1, "limit": page_size}, timeout=30)
        r.raise_for_status()
        data = _safe_get_json(r)
        # Messari v2 returns {"status": {..}, "data": [{..}, ...]}
        items = data.get("data", []) if isinstance(data, dict) else []
        return items if isinstance(items, list) else []
    except Exception as e:
        logging.error(f"❌ Messari fetch failed: {e}")
        return []
