# scanner_tier2.py
import os
import logging
import json
from db import supabase, insert_signal, upsert_signal
from services.providers import get_ohlcv_coin_gecko, get_top_markets
from technical_indicators import compute_metrics
from datetime import datetime

TIER1_FILE = os.getenv("TIER1_OUTPUT_FILE", "tier1_symbols.txt")

# Basic AI scoring heuristic (placeholder for actual model)
def compute_ai_score(metrics: dict) -> (float, str):
    """Return (score 0-10, short_reason). Deterministic heuristic: favors rvol>2, RSI between 50-70, EMA align."""
    score = 0.0
    reasons = []
    rvol = metrics.get("rvol") or 0
    rsi = metrics.get("rsi") or 0
    ema5 = metrics.get("ema5")
    ema13 = metrics.get("ema13")
    ema50 = metrics.get("ema50")

    # RVOL
    score += min(max((rvol - 1) * 3, 0), 4)  # up to 4 points

    # RSI preference
    if 50 <= rsi <= 70:
        score += 2.0
        reasons.append("RSI in bullish range")
    elif rsi > 70:
        score += 0.5
        reasons.append("RSI high")

    # EMA alignment
    if ema5 and ema13 and ema50:
        if ema5 > ema13 > ema50:
            score += 2.0
            reasons.append("Bullish EMA alignment")

    # Cap
    score = min(score, 10.0)
    reason_text = " + ".join(reasons) if reasons else "Metrics indicate cautious interest"
    return round(score, 2), reason_text

def risk_panel(latest_close: float, atr: float):
    sl = latest_close - 1.5 * (atr or 0)
    tp = latest_close + 3 * (atr or 0)
    position_size = None  # user-specific; placeholder
    return {"entry": latest_close, "stop_loss": max(sl, 0), "take_profit": tp, "position_size": position_size}

def symbols_from_tier1_file():
    if os.path.exists(TIER1_FILE):
        with open(TIER1_FILE, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
            return lines
    return []

def fallback_top_candidates(limit=50):
    markets = get_top_markets(limit=limit)
    return [m.get("id") for m in markets]

def main():
    logging.basicConfig(level=logging.INFO)
    symbols = symbols_from_tier1_file()
    if not symbols:
        logging.info("No tier1 file found; attempting to pull candidates from Supabase or top markets.")
        if supabase:
            try:
                res = supabase.table("signals").select("coin_id").limit(200).execute()
                data = res.data if hasattr(res, "data") else res
                symbols = [row.get("coin_id") for row in data if row.get("coin_id")]
            except Exception:
                logging.exception("Supabase query failed; falling back to top markets")
                symbols = fallback_top_candidates(limit=50)
        else:
            symbols = fallback_top_candidates(limit=50)

    logging.info("Tier2 running on %d symbols", len(symbols))

    results = []
    for coin_id in symbols:
        try:
            df = get_ohlcv_coin_gecko(coin_id, days=7)
            if df.empty:
                logging.warning("No OHLCV for %s; skipping", coin_id)
                continue
            metrics = compute_metrics(df)
            latest_close = float(df["close"].iloc[-1])
            ai_score, ai_reason = compute_ai_score(metrics)
            rp = risk_panel(latest_close, metrics.get("atr"))

            payload = {
                "ticker": coin_id,
                "coin_id": coin_id,
                "time": datetime.utcnow().isoformat(),
                "price": latest_close,
                "rsi": metrics.get("rsi"),
                "ema5": metrics.get("ema5"),
                "ema13": metrics.get("ema13"),
                "ema50": metrics.get("ema50"),
                "vwap": metrics.get("vwap"),
                "atr": metrics.get("atr"),
                "rvol": metrics.get("rvol"),
                "volume": metrics.get("volume"),
                "ai_score": ai_score,
                "ai_reason": ai_reason,
                "risk": rp,
                "tier": "tier2"
            }

            # upsert to supabase for dashboard
            try:
                upsert_signal(payload, on_conflict="coin_id")
            except Exception:
                logging.exception("Failed to upsert to supabase for %s", coin_id)

            results.append(payload)
            logging.info("Processed %s ai_score=%s rsi=%s rvol=%s", coin_id, ai_score, metrics.get("rsi"), metrics.get("rvol"))
        except Exception as e:
            logging.exception("Error processing %s: %s", coin_id, e)

    # Save local results for debugging/view (optional)
    with open("tier2_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Tier2 finished. Results: {len(results)}")
    # Optionally: send Telegram alerts here (not included to keep this focused)

if __name__ == "__main__":
    main()
