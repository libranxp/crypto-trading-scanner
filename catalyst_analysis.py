# catalyst_analysis.py
from typing import Dict, Any, List

def pick_best_catalyst(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Choose the catalyst with highest impact heuristic (source + engagement + recency).
    """
    if not candidates:
        return {}
    ranked = sorted(
        candidates,
        key=lambda c: (c.get("impact", 0), c.get("engagement", 0), c.get("ts", 0)),
        reverse=True
    )
    return ranked[0]

def catalyst_summary(best: Dict[str, Any]) -> str:
    if not best:
        return "No strong catalyst detected."
    source = best.get("source", "News")
    title = best.get("title") or best.get("summary") or "Update"
    return f'{source}: "{title}"'
