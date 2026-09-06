"""
StockSense AI — Backtest Reproducibility & Configuration Hashing
Computes cryptographic SHA-256 configuration hashes to guarantee deterministic repeatability.
"""

import hashlib
import json
from app.backtesting.schemas import BacktestConfig


def generate_configuration_hash(config: BacktestConfig) -> str:
    """
    Computes a canonical SHA-256 hash of the backtest parameters.
    """
    config_dict = config.model_dump() if hasattr(config, "model_dump") else config.dict()
    # Canonical JSON string with sorted keys
    canonical_str = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
