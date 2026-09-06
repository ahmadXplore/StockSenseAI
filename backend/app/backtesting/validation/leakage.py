"""
StockSense AI — Look-Ahead Bias & Information Leakage Guard
Asserts that no price, feature, prediction, or corporate action from future timestamp (T > t) influences decisions at time t.
"""

from typing import Dict, Any, List


class LookaheadAuditException(Exception):
    pass


def assert_no_lookahead_leakage(
    current_decision_date: str,
    feature_timestamp: str,
    price_timestamp: str,
    prediction_timestamp: Optional[str] = None,
) -> bool:
    """
    Validates that all input timestamps are strictly <= decision timestamp.
    Raises LookaheadAuditException if leakage is detected.
    """
    if feature_timestamp > current_decision_date:
        raise LookaheadAuditException(
            f"LOOKAHEAD BIAS DETECTED: Feature timestamp ({feature_timestamp}) is in the future relative to decision date ({current_decision_date})."
        )

    if price_timestamp > current_decision_date:
        raise LookaheadAuditException(
            f"LOOKAHEAD BIAS DETECTED: Price bar timestamp ({price_timestamp}) is after decision date ({current_decision_date})."
        )

    if prediction_timestamp and prediction_timestamp > current_decision_date:
        raise LookaheadAuditException(
            f"LOOKAHEAD BIAS DETECTED: ML prediction timestamp ({prediction_timestamp}) is after decision date ({current_decision_date})."
        )

    return True
