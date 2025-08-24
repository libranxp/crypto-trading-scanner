import logging
from technical_indicators import compute_technical_metrics

logger = logging.getLogger(__name__)

def tier2_analysis_for_coin(coin_info: dict) -> dict:
    """
    coin_info must include 'id' (coingecko id) and 'price'.
    Returns extended analysis with ai_score and risk.
    """
    coin_id = coin_info.get("id")
    price = coin_info.get("price", 0.0)

    # compute technical metrics again (deeper window)
    tech = compute_technical_metrics(coin_id, current_price=price)
    rsi = tech.get("rsi", 60.0)
    rvol = tech.get("rvol", 1.0)
    ema_aligned = tech.get("ema_aligned", False)
    vwap_prox = tech.get("vwap_proximity", 0.0)

    # Placeholder sentiment: you can wire LunarCrush/Santiment/Twitter here.
    sentiment_score = coin_info.get("sentiment_score", 0.6)

    # Simple AI score (heuristic)
    ai_score = (max(0, (70 - abs(60 - rsi)))  # rewards RSI near 60
               + min(50, (rvol - 1.0) * 20)   # rewards RVOL
               + (20 if ema_aligned else 0)
               + (10 * sentiment_score))

    # risk: simple buckets
    if ai_score >= 80:
        risk = "Low"
    elif ai_score >= 60:
        risk = "Medium"
    else:
        risk = "High"

    return {
        **coin_info,
        "rsi": rsi,
        "rvol": rvol,
        "ema_aligned": ema_aligned,
        "vwap_proximity": vwap_prox,
        "sentiment_score": sentiment_score,
        "ai_score": round(ai_score, 2),
        "risk": risk
    }
