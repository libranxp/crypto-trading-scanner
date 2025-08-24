import logging
from typing import Any, Dict, List
from config import PRICE_MIN, PRICE_MAX, VOL_MIN, MCAP_MAX
from services.providers import fetch_cmc, fetch_lunarcrush, fetch_messari
from db import supabase, TABLE

def _num(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def _normalize_cmc(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for item in rows:
        if not isinstance(item, dict):
            logging.warning("⚠️ Skipping invalid CMC entry: not a dict")
            continue
        symbol = item.get("symbol")
        quote = item.get("quote") or {}
        usd = quote.get("USD") if isinstance(quote, dict) else {}
        price = _num((usd or {}).get("price"))
        vol   = _num((usd or {}).get("volume_24h"))
        mcap  = _num((usd or {}).get("market_cap"))
        chg   = _num((usd or {}).get("percent_change_24h"))
        if not symbol:
            continue
        out.append({
            "symbol": symbol,
            "price": price,
            "volume": vol,
            "market_cap": mcap,
            "change_24h": chg,
            "source": "CMC"
        })
    return out

def _normalize_lunar(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for item in rows:
        if not isinstance(item, dict):
            logging.warning("⚠️ Skipping invalid LunarCrush entry: not a dict")
            continue
        symbol = item.get("s")
        price = _num(item.get("p"))
        vol   = _num(item.get("v"))
        mcap  = _num(item.get("mc"))
        chg   = _num(item.get("pchg"))
        if not symbol:
            continue
        out.append({
            "symbol": symbol,
            "price": price,
            "volume": vol,
            "market_cap": mcap,
            "change_24h": chg,
            "source": "LUNAR"
        })
    return out

def _normalize_messari(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for item in rows:
        if not isinstance(item, dict):
            logging.warning("⚠️ Skipping invalid Messari entry: not a dict")
            continue
        symbol = item.get("symbol") or item.get("slug")
        metrics = item.get("metrics", {})
        mdata = (metrics or {}).get("market_data", {}) if isinstance(metrics, dict) else {}
        mcap_bag = (metrics or {}).get("marketcap", {}) if isinstance(metrics, dict) else {}
        price = _num(mdata.get("price_usd"))
        vol   = _num(mdata.get("volume_last_24_hours"))
        mcap  = _num(mcap_bag.get("current_marketcap_usd"))
        chg   = _num(mdata.get("percent_change_usd_last_24_hours"))
        if not symbol:
            continue
        out.append({
            "symbol": symbol.upper() if isinstance(symbol, str) else symbol,
            "price": price,
            "volume": vol,
            "market_cap": mcap,
            "change_24h": chg,
            "source": "MESSARI"
        })
    return out

def _apply_filters(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = []
    for r in rows:
        price = _num(r.get("price"))
        vol   = _num(r.get("volume"))
        mcap  = _num(r.get("market_cap"))
        if price is None or vol is None or mcap is None:
            continue
        if PRICE_MIN < price < PRICE_MAX and vol > VOL_MIN and mcap < MCAP_MAX:
            filtered.append(r)
    return filtered

def run_auto_scan() -> List[Dict[str, Any]]:
    logging.info("🚀 Running auto scan…")

    cmc_raw    = fetch_cmc()
    lunar_raw  = fetch_lunarcrush()
    messari_raw= fetch_messari()

    cmc_n      = _normalize_cmc(cmc_raw)
    lunar_n    = _normalize_lunar(lunar_raw)
    messari_n  = _normalize_messari(messari_raw)

    merged     = cmc_n + lunar_n + messari_n
    cleaned    = [r for r in merged if isinstance(r, dict) and r.get("symbol")]

    screened   = _apply_filters(cleaned)

    # Deduplicate by symbol, preferring first occurrence
    seen = set()
    unique = []
    for r in screened:
        sym = r["symbol"]
        if sym in seen:
            continue
        seen.add(sym)
        unique.append(r)

    if unique:
        # Upsert using (symbol, source, price, volume, market_cap, change_24h)
        # Create table with at least columns: id (bigint PK), symbol text, price numeric, volume numeric,
        # market_cap numeric, change_24h numeric, source text, created_at timestamp default now()
        try:
            supabase.table(TABLE).insert(unique).execute()
            logging.info(f"✅ Saved {len(unique)} rows to Supabase.")
        except Exception as e:
            logging.error(f"❌ Supabase insert failed: {e}")

    return unique
