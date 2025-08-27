import math
import os
from typing import Dict, List

from config import (
    MAX_MARKETS_TO_SCAN, MAX_TIER2_DEEP_CANDLES, QUOTE_CCY,
    PRICE_MIN, PRICE_MAX, VOL_MIN, MCAP_MIN, MCAP_MAX,
    CHANGE_MIN_PCT, CHANGE_MAX_PCT, RSI_MIN, RSI_MAX,
    RVOL_MIN, VWAP_PROX_PCT, SOCIAL_MENTIONS_MIN, ENGAGEMENT_MIN,
    SENTIMENT_MIN, REJECT_PUMP_PCT
)
from services.providers import (
    get_market_list_cmc, get_ohlcv_polygon,
    get_social_lunarcrush, get_news_links, tradingview_link
)
from technical_indicators import compute_technical_metrics
from telegram_alerts import send_telegram_alert
from duplicate_cache import seen_recent, mark_seen

def pct(a: float, b: float) -> float:
    if b == 0 or a is None or b is None: return 0.0
    return (a - b) / b * 100.0

def _pump_filter(ohlcv: List[Dict], threshold_pct: float = 50.0) -> bool:
    """Reject if any 60-min window has > threshold% rise."""
    if not ohlcv or len(ohlcv) < 12:  # with 5-min candles
        return False
    # check last 12 bars (~1h)
    first = ohlcv[-12]["c"]
    last = ohlcv[-1]["c"]
    return pct(last, first) > threshold_pct

def _ai_score(features: Dict) -> (float, str, str):
    """Lightweight deterministic scorer (0–10) + confidence + short narrative."""
    score = 0.0
    reason = []
    # RSI sweet spot
    if RSI_MIN <= features["rsi"] <= RSI_MAX:
        score += 2.0; reason.append("RSI in accumulation zone")
    # EMA stack
    if features["ema5"] > features["ema13"] > features["ema50"]:
        score += 2.0; reason.append("EMA5>EMA13>EMA50 trend")
    # VWAP proximity
    vwap_dev = abs(features["close"] - features["vwap"]) / features["vwap"] * 100 if features["vwap"] else 999
    if vwap_dev <= VWAP_PROX_PCT:
        score += 1.5; reason.append("Near VWAP")
    # RVOL
    if features["rvol"] >= RVOL_MIN:
        score += 2.0; reason.append("Elevated RVOL")
    # Sentiment
    if features["sentiment"] >= 0.6:
        score += 1.5; reason.append("Positive social sentiment")
    # Price change moderation (2–20 already enforced)
    score += 1.0  # base prior for meeting Tier 1 filters

    # Clip 0–10
    score = max(0.0, min(10.0, score))
    conf = "High" if score >= 7.5 else ("Medium" if score >= 5.0 else "Low")
    narrative = " + ".join(reason) if reason else "Meets core momentum filters"
    return score, conf, narrative

def _risk_panel(close: float, atr: float) -> Dict:
    """ATR-based SL/TP with simple 1R/2R."""
    if not (close and atr and atr > 0):
        return {"stop_loss": None, "take_profit": None, "position_size": "—"}
    sl = close - 1.5 * atr
    tp = close + 3.0 * atr
    # Position sizing placeholder (1% risk of $10k account)
    account = 10_000.0
    risk_per_trade = 0.01 * account
    per_unit_risk = close - sl if sl and close else None
    qty = max(0, int(risk_per_trade / per_unit_risk)) if per_unit_risk and per_unit_risk > 0 else 0
    return {"stop_loss": sl, "take_profit": tp, "position_size": qty}

def _passes_tier1(d: Dict) -> bool:
    price = d.get("price") or 0
    vol = d.get("volume_24h") or 0
    mcap = d.get("market_cap") or 0
    chg = d.get("percent_change_24h") or 0
    return (
        PRICE_MIN <= price <= PRICE_MAX and
        vol >= VOL_MIN and
        MCAP_MIN <= mcap <= MCAP_MAX and
        CHANGE_MIN_PCT <= chg <= CHANGE_MAX_PCT
    )

def _passes_tier2(symbol: str, ohlcv: List[Dict], tech: Dict, social: Dict) -> bool:
    if not tech: return False
    if _pump_filter(ohlcv, REJECT_PUMP_PCT): return False
    if not (RSI_MIN <= tech["rsi"] <= RSI_MAX): return False
    if not (tech["ema5"] > tech["ema13"] > tech["ema50"]): return False
    # vwap proximity
    if tech["vwap"] and abs(tech["close"] - tech["vwap"]) / tech["vwap"] * 100 > VWAP_PROX_PCT:
        return False
    if not (tech["rvol"] and tech["rvol"] >= RVOL_MIN): return False
    if not (social.get("mentions", 0) >= SOCIAL_MENTIONS_MIN): return False
    if not (social.get("engagement", 0) >= ENGAGEMENT_MIN): return False
    if not (social.get("sentiment", 0.0) >= SENTIMENT_MIN): return False
    return True

def run_auto_tier2() -> List[Dict]:
    markets = get_market_list_cmc(limit=MAX_MARKETS_TO_SCAN)
    shortlisted = [m for m in markets if _passes_tier1(m) and not seen_recent(m["symbol"])]
    results: List[Dict] = []

    for m in shortlisted:
        sym = m["symbol"]
        try:
            ohlcv = get_ohlcv_polygon(sym, multiplier=5, timespan="minute", limit=MAX_TIER2_DEEP_CANDLES)
            if not ohlcv: continue
            tech = compute_technical_metrics(ohlcv)
            social = get_social_lunarcrush(sym)
            if not _passes_tier2(sym, ohlcv, tech, social):
                continue

            ai_score, ai_conf, ai_reason = _ai_score({
                **tech,
                "sentiment": social.get("sentiment", 0.0),
            })
            risk = _risk_panel(tech.get("close"), tech.get("atr"))

            links = {
                "tradingview": tradingview_link(sym),
                "news": get_news_links(sym, max_items=2),
                "reddit": [],  # can be filled later
                "tweet": [],   # can be filled later
                "catalyst": get_news_links(sym, max_items=1),
            }

            payload = {
                "symbol": sym,
                "name": m.get("name"),
                "price": tech.get("close") or m.get("price"),
                "change_pct": m.get("percent_change_24h"),
                "rsi": tech.get("rsi"),
                "ema5": tech.get("ema5"),
                "ema13": tech.get("ema13"),
                "ema50": tech.get("ema50"),
                "vwap": tech.get("vwap"),
                "atr": tech.get("atr"),
                "rvol": tech.get("rvol"),
                "volume": tech.get("volume"),
                "ai_score": ai_score,
                "ai_confidence": ai_conf,
                "ai_reason": ai_reason,
                "risk": risk,
                "sentiment": {
                    "score": social.get("sentiment", 0.0),
                    "mentions": social.get("mentions", 0),
                    "engagement": social.get("engagement", 0),
                    "influencer": social.get("influencer", False),
                },
                "links": links,
                "quote": QUOTE_CCY,
            }

            # Alert + mark seen
            send_telegram_alert(payload)
            mark_seen(sym)
            results.append(payload)

        except Exception as e:
            # Best-effort; continue scanning others
            continue

    return results

if __name__ == "__main__":
    out = run_auto_tier2()
    # Print summary for GitHub Actions log (kept minimal)
    print(f"Tier 2 candidates: {len(out)}")
    for r in out:
        print(f"- {r['symbol']} | AI {r['ai_score']:.1f} | RSI {r['rsi']:.1f} | RVOL {r['rvol']:.2f}")
