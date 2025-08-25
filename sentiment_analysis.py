# sentiment_analysis.py
from typing import Dict, Any, List
import math

def aggregate_sentiment(lunar: Dict[str, Any], santiment: Dict[str, Any], reddit: Dict[str, Any], twitter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize each to 0..1 and average with simple weights.
    """
    def norm(x, lo=0, hi=1):
        if x is None: return None
        return max(0.0, min(1.0, (x - lo) / (hi - lo))) if hi != lo else 0.0

    scores = []
    detail = {}

    if lunar and "galaxy_score" in lunar:
        s = norm(lunar["galaxy_score"]/100.0)  # LunarCrush Galaxy 0..100
        scores.append(s)
        detail["lunarcrush"] = s

    if santiment and "sentiment" in santiment:
        s = norm((santiment["sentiment"]+1)/2)  # map -1..1 -> 0..1
        scores.append(s)
        detail["santiment"] = s

    if reddit and "engagement" in reddit:
        s = norm(min(1.0, reddit["engagement"]/500.0))  # crude cap
        scores.append(s)
        detail["reddit"] = s

    if twitter and "engagement" in twitter:
        s = norm(min(1.0, twitter["engagement"]/1000.0))
        scores.append(s)
        detail["twitter"] = s

    score = sum(scores)/len(scores) if scores else None
    label = "Bullish" if score is not None and score >= 0.6 else ("Bearish" if score is not None and score <= 0.4 else "Neutral")
    return {"score": score, "label": label, "detail": detail}

def influencer_flag(twitter: Dict[str, Any]) -> bool:
    return bool(twitter and twitter.get("influencer_hit", False))
