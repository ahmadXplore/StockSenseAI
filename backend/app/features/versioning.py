"""
StockSense AI — Feature Versioning & Configuration Hasher
Guarantees full reproducibility of generated feature matrices.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


@dataclass
class FeatureVersionConfig:
    feature_set_id: str
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    feature_names: List[str] = field(default_factory=list)
    extractor_parameters: Dict[str, Any] = field(default_factory=dict)
    source_data_versions: Dict[str, str] = field(default_factory=dict)
    config_hash: str = ""

    def __post_init__(self):
        if not self.config_hash:
            self.config_hash = self.generate_hash()

    def generate_hash(self) -> str:
        """Generates a SHA-256 fingerprint from the feature configuration parameters."""
        payload = {
            "feature_set_id": self.feature_set_id,
            "version": self.version,
            "features": sorted(self.feature_names),
            "parameters": self.extractor_parameters,
            "source_data_versions": self.source_data_versions,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]
