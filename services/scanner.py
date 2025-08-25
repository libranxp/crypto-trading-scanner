# services/scanner.py
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
import math
import logging

from config import FILTERS, TOP_N_TIER1, MAX_ALERTS_PER_SCAN, CANDLES_LOOKBACK, RISK
from db import upsert_scan_rows
from services import providers
from technical_indicators import rsi, ema, atr, vwap, rvol, ema_alignment
from sentiment_analysis import aggregate_sentiment, influencer_flag
from catalyst_analysis import pick_best_catalyst, catalyst_summary
from duplicate_cache import should_suppress, mark_alert
from telegram_alerts import send_alert

logger = logging.getLogger(__name__)

def _within(x, lo, hi):
    try:
        return x is not None and lo <= x <= hi
    except:
        return False

def _pct(a, b):
    return (a - b) / b * 100.0 if (a is not None and b not in (None, 0)) else None

def _ai_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight surrogate "RF" style scoring without heavy model deps:
    Sum of weighted rules -> 0..10, with narrative.
    """
    score = 0.0
    reasons = []

    # Momentum window
    if 2 <= features.get("pct_change_24h", 0) <= 20:
        score += 2.0; reasons.append("Healthy 24h momentum")

    # RSI sweet spot
    if 50 <= features.get("rsi", 0) <= 70:
        score += 1.5; reasons.append("RSI in accumulation zone")

    # EMA stack
    if features.get("ema_aligned"):
        score += 1.5; reasons.append("EMA5>EMA13>EMA50 alignment")

    # VWAP proximity
    if abs(features.get("vwap_delta_pct", 99)) <= 2:
        score += 1.0; reasons.append("Near VWAP")

    # RVOL
    if features.get("rvol", 0) >= 2:
        score += 1.5; reasons.append("RVOL > 2x")

    # Sentiment & influencer
    sent = features.get("sentiment_score", 0)
    if sent >= 0.6: score += 1.5; reasons.append("Bullish sentiment")
    if features.get("influencer_hit"): score += 1.0; reasons.append("Influencer mention")

    # Liquidity & MCAP safety
    if features.get("volume_24h", 0) >= 10_000_000: score += 0.5
    if 10_000_000 <= features.get("market_cap", 0) <= 5_000_000_000: score += 0.5

    score = max(0.0, min(10.0, score))
    narrative = " + ".join(reasons) if reasons else "Pattern confluence"
    conf = "High" if score >= 7.5 else ("Medium" if score >= 5.0 else "Low")
    return {"score": score, "confidence": conf, "narrative": narrative}

def _risk(prices: List[float], highs: List[float], lows: List[float], atr_vals: List[float], equity_usd: float = 10000.0) -> Dict[str, Any]:
    last_close = prices[-1]
    last_atr = next((x for x in reversed(atr_vals) if x is not None), None)
    if last_atr is None:
        # fallback 2% risk bands
        sl = last_close * 0.98
        tp = last_close * 1.04
        risk_amt = equity_usd * (RISK["risk_per_trade_pct"]/100.0)
        pos_size = risk_amt / (last_close - sl) if last_close > sl else risk_amt/ (0.02*last_close)
        return {"stop_loss": sl, "take_profit": tp, "position_size": pos_size}

    sl = last_close - RISK["atr_sl_mult"] * last_atr
    tp = last_close + RISK["atr_tp_mult"] * last_atr
    risk_amt = equity_usd * (RISK["risk_per_trade_pct"]/100.0)
    pos_size = risk_amt / (last_close - sl) if last_close > sl else risk_amt / max(1e-6, last_atr)
    return {"stop_loss": sl, "take_profit": tp, "position_size": pos_size}

def _passes_filters(row: Dict[str, Any]) -> bool:
    f = FILTERS
    return (
        _within(row["price"], f["price_min"], f["price_max"]) and
        row["volume_24h"] is not None and row["volume_24h"] >= f["vol_24h_min"] and
        _within(row["pct_change_24h"], f["pct_change_min"], f["pct_change_max"]) and
        _within(row["market_cap"], f["mcap_min"], f["mcap_max"]) and
        _within(row["rsi"], f["rsi_min"], f["rsi_max"]) and
        row["rvol"] is not None and row["rvol"] >= f["rvol_min"] and
        (row["ema_aligned"] if f["ema_alignment"] else True) and
        abs(row["vwap_delta_pct"]) <= f["vwap_proximity_pct"] and
        row["pump_reject"] is False and
        row["twitter_mentions"] >= f["twitter_mentions_min"] and
        row["engagement"] >= f["engagement_min"] and
        (row["influencer_hit"] if f["influencer_required"] else True) and
        (row["sentiment_score"] is not None and row["sentiment_score"] >= f["sentiment_min"])
    )

def _tv_link(symbol: str) -> str:
    return f"https://www.tradingview.com/symbols/{symbol}USD/"

def run_auto_scan() -> List[Dict[str, Any]]:
    markets = providers.list_markets(limit=300)
    symbols = [m["symbol"] for m in markets if m.get("symbol")]
    quotes = providers.get_quote(symbols)

    rows: List[Dict[str, Any]] = []
    for sym in symbols:
        q = quotes.get(sym)
        if not q: continue

        ohlcv = providers.get_ohlcv(sym, CANDLES_LOOKBACK)
        if not ohlcv: continue
        closes = ohlcv["close"]; highs = ohlcv["high"]; lows = ohlcv["low"]; vols = ohlcv["volume"]
        if len(closes) < 60: continue

        rsi_vals = rsi(closes, 14)
        ema5 = ema(closes, 5)
        ema13 = ema(closes, 13)
        ema50 = ema(closes, 50)
        atr_vals = atr(highs, lows, closes, 14)
        vwap_vals = vwap(highs, lows, closes, vols)
        rvol_vals = rvol(vols, 20)

        last = len(closes)-1
        last_price = closes[last]
        last_rsi = rsi_vals[last] if rsi_vals and rsi_vals[last] is not None else None
        last_ema5 = ema5[last] if ema5 else None
        last_ema13 = ema13[last] if ema13 else None
        last_ema50 = ema50[last] if ema50 else None
        last_vwap = vwap_vals[last] if vwap_vals else None
        last_rvol = rvol_vals[last] if rvol_vals else None

        vwap_delta_pct = _pct(last_price, last_vwap) if last_vwap else 999.0
        ema_ok = ema_alignment(last_ema5, last_ema13, last_ema50)

        # Pump filter (past 4 bars)
        recent = closes[-4:]
        pump_pct = _pct(recent[-1], recent[0]) if recent and recent[0] else 0
        pump_reject = pump_pct is not None and pump_pct > FILTERS["pump_reject_pct"]

        # Basic social/sentiment (cheap)
        lunar = providers.get_lunarcrush(sym)
        reddit = providers.get_reddit(sym)
        twitter = providers.get_twitter(sym)
        sentiment = aggregate_sentiment(lunar, {}, reddit, twitter)
        infl = influencer_flag(twitter)
        mentions = twitter.get("mentions", 0)
        engagement = twitter.get("engagement", 0) + reddit.get("engagement", 0)

        row = {
            "symbol": sym,
            "price": q["price"],
            "pct_change_24h": q["pct_change_24h"],
            "market_cap": q["market_cap"],
            "volume_24h": q["volume_24h"],
            "rsi": last_rsi,
            "ema5": last_ema5, "ema13": last_ema13, "ema50": last_ema50,
            "ema_aligned": ema_ok,
            "vwap": last_vwap, "vwap_delta_pct": vwap_delta_pct if vwap_delta_pct is not None else 999.0,
            "atr": atr_vals[last] if atr_vals and atr_vals[last] is not None else None,
            "rvol": last_rvol if last_rvol is not None else None,
            "pump_reject": pump_reject,
            "twitter_mentions": mentions,
            "engagement": engagement,
            "influencer_hit": infl,
            "sentiment_score": sentiment.get("score"),
            "sentiment_label": sentiment.get("label"),
            "timestamp": int(time.time()),
            "tradingview_url": _tv_link(sym),
        }

        if _passes_filters(row):
            rows.append(row)

    # keep top N by engagement + volume
    rows = sorted(rows, key=lambda r: (r["engagement"], r["volume_24h"]), reverse=True)[:TOP_N_TIER1]
    upsert_scan_rows(rows)
    return rows

def run_manual_scan(symbols: List[str]) -> List[Dict[str, Any]]:
    """Tier-2 deep analysis; if empty list provided, run on top Tier-1 picks."""
    if not symbols:
        tier1 = run_auto_scan()
        symbols = [r["symbol"] for r in tier1[:MAX_ALERTS_PER_SCAN]]

    out = []
    for sym in symbols:
        ohlcv = providers.get_ohlcv(sym, CANDLES_LOOKBACK)
        if not ohlcv: continue
        closes = ohlcv["close"]; highs = ohlcv["high"]; lows = ohlcv["low"]; vols = ohlcv["volume"]
        rsi_vals = rsi(closes, 14); ema5 = ema(closes,5); ema13=ema(closes,13); ema50=ema(closes,50)
        atr_vals = atr(highs, lows, closes, 14); vwap_vals = vwap(highs,lows,closes,vols); rvol_vals=rvol(vols,20)
        i = len(closes)-1
        last_price = closes[i]
        features = {
            "pct_change_24h": None,  # filled from quotes below
            "rsi": rsi_vals[i] if rsi_vals[i] is not None else 50.0,
            "ema_aligned": ema_alignment(ema5[i], ema13[i], ema50[i]),
            "vwap_delta_pct": _pct(last_price, vwap_vals[i]) if vwap_vals[i] else 99.0,
            "rvol": rvol_vals[i] if rvol_vals[i] is not None else 1.0,
            "market_cap": None, "volume_24h": None,
            "sentiment_score": None, "influencer_hit": False
        }

        # Enrich
        q = providers.get_quote([sym]).get(sym, {})
        features["pct_change_24h"] = q.get("pct_change_24h", 0)
        features["market_cap"] = q.get("market_cap", 0)
        features["volume_24h"] = q.get("volume_24h", 0)

        lunar = providers.get_lunarcrush(sym)
        sant = providers.get_santiment(sym)
        reddit = providers.get_reddit(sym)
        twitter = providers.get_twitter(sym)
        sent = aggregate_sentiment(lunar, sant, reddit, twitter)
        features["sentiment_score"] = sent.get("score", 0.5)
        features["influencer_hit"] = influencer_flag(twitter)

        # AI scoring
        ai = _ai_score(features)

        # Risk
        risk = _risk(closes, highs, lows, atr_vals)

        # News/catalyst
        news = providers.get_news(sym)
        best = pick_best_catalyst(news)

        payload = {
            "symbol": sym,
            "price": last_price,
            "pct_change_24h": features["pct_change_24h"],
            "ai_score": ai["score"],
            "ai_confidence": ai["confidence"],
            "ai_narrative": ai["narrative"],
            "risk": risk,
            "sentiment": {"score": sent.get("score"), "label": sent.get("label")},
            "sentiment_links": [],  # could add per-source links if you store them
            "catalyst": best,
            "catalyst_summary": catalyst_summary(best),
            "tradingview_url": f"https://www.tradingview.com/symbols/{sym}USD/",
            "news_url": (news[0]["url"] if news else None),
            "reddit_url": "https://reddit.com/r/cryptocurrency",
            "tweet_url": "https://twitter.com/",
            "time_str": datetime.now(timezone.utc).strftime("📅 Time: %H:%M UTC"),
            # For dashboard fields:
            "rsi": features["rsi"],
            "ema5": ema5[i], "ema13": ema13[i], "ema50": ema50[i],
            "vwap": vwap_vals[i] if vwap_vals else None,
            "atr": atr_vals[i] if atr_vals else None,
            "rvol": features["rvol"],
            "volume_24h": features["volume_24h"],
            "market_cap": features["market_cap"],
        }

        out.append(payload)

    return out

def scan_and_alert() -> List[Dict[str, Any]]:
    tier1 = run_auto_scan()
    # Pick candidates for alerts (not alerted in last 6h)
    candidates = [r for r in tier1 if not should_suppress(r["symbol"])]
    selected = candidates[:MAX_ALERTS_PER_SCAN]
    detailed = run_manual_scan([r["symbol"] for r in selected])
    for d in detailed:
        send_alert(d)
        mark_alert(d["symbol"])
    return detailed
