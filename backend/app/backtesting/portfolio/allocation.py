"""
StockSense AI — Portfolio Allocation Engine
Implements target weight allocations: Equal-Weight, Inverse-Vol, Market-Cap, AI-Confidence, Risk-Parity.
"""

from typing import List, Dict, Optional
import numpy as np
from app.backtesting.schemas import AllocationMethod


def compute_target_allocations(
    securities: List[str],
    method: AllocationMethod = AllocationMethod.EQUAL_WEIGHT,
    volatilities: Optional[Dict[str, float]] = None,
    market_caps: Optional[Dict[str, float]] = None,
    ai_confidences: Optional[Dict[str, float]] = None,
    ai_expected_returns: Optional[Dict[str, float]] = None,
    max_position_weight: float = 0.25,
    min_position_weight: float = 0.01,
) -> Dict[str, float]:
    """
    Computes target portfolio weights normalized to sum to 1.0 (or cash fraction).
    """
    n = len(securities)
    if n == 0:
        return {}
    if n == 1:
        return {securities[0]: min(1.0, max_position_weight)}

    raw_weights: Dict[str, float] = {}

    if method == AllocationMethod.EQUAL_WEIGHT:
        w = 1.0 / n
        for s in securities:
            raw_weights[s] = w

    elif method == AllocationMethod.INVERSE_VOLATILITY:
        vols = volatilities or {}
        inv_vols = {s: (1.0 / max(0.01, vols.get(s, 0.20))) for s in securities}
        total_inv = sum(inv_vols.values()) or 1.0
        for s in securities:
            raw_weights[s] = inv_vols[s] / total_inv

    elif method == AllocationMethod.MARKET_CAP_WEIGHT:
        caps = market_caps or {}
        total_cap = sum(caps.get(s, 1e9) for s in securities) or 1.0
        for s in securities:
            raw_weights[s] = caps.get(s, 1e9) / total_cap

    elif method == AllocationMethod.AI_CONFIDENCE:
        confs = ai_confidences or {}
        total_conf = sum(max(0.1, confs.get(s, 0.5)) for s in securities) or 1.0
        for s in securities:
            raw_weights[s] = max(0.1, confs.get(s, 0.5)) / total_conf

    elif method == AllocationMethod.AI_EXPECTED_RETURN:
        rets = ai_expected_returns or {}
        pos_rets = {s: max(0.001, rets.get(s, 0.05)) for s in securities}
        total_ret = sum(pos_rets.values()) or 1.0
        for s in securities:
            raw_weights[s] = pos_rets[s] / total_ret

    else:
        # Default equal weight
        w = 1.0 / n
        for s in securities:
            raw_weights[s] = w

    # Apply maximum and minimum constraints with iterative renormalization
    capped_weights: Dict[str, float] = {}
    for s, w in raw_weights.items():
        capped_weights[s] = min(max_position_weight, max(min_position_weight, w))

    # Re-normalize to sum to <= 1.0
    total_w = sum(capped_weights.values())
    if total_w > 1.0:
        for s in capped_weights:
            capped_weights[s] = round(capped_weights[s] / total_w, 4)

    return capped_weights
