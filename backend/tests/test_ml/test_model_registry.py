"""
Unit Tests for Model Registry & Artifact Store
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from app.ml.models.direction import DirectionClassifier
from app.ml.registry.model_registry import ModelRegistry


def test_model_registry_save_load_checksum():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = ModelRegistry(storage_dir=tmp_dir)

        clf = DirectionClassifier(model_id="test_clf_1", horizon="30d")
        X = pd.DataFrame({"f1": [1.0, 2.0, 3.0], "f2": [4.0, 5.0, 6.0]})
        y = pd.Series([0, 1, 0])
        clf.fit(X, y)

        # Save model
        rec = registry.save_model(clf, metrics={"accuracy": 85.0}, status="VALIDATED")
        assert rec.model_id == "test_clf_1"
        assert len(rec.artifact_hash) == 64 # SHA-256 hash length

        # Load model and verify integrity
        loaded = registry.load_model("test_clf_1")
        assert loaded is not None
        assert loaded.model_id == "test_clf_1"
        assert loaded.is_fitted is True

        # Promote to deployed
        assert registry.promote_to_deployed("test_clf_1") is True
        deployed = registry.get_deployed_model("US", "NASDAQ", "30d")
        assert deployed is not None
