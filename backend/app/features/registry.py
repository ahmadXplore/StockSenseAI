"""
StockSense AI — Feature Registry
Central registry for discovering, registering, and orchestrating feature extractors.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Type
import pandas as pd
from app.features.base import BaseFeatureExtractor, FeatureContext, FeatureCategory


class FeatureRegistry:
    """
    Registry for managing all point-in-time feature extractors.
    """

    def __init__(self):
        self._extractors: Dict[str, BaseFeatureExtractor] = {}

    def register(self, extractor: BaseFeatureExtractor) -> BaseFeatureExtractor:
        """Registers a feature extractor instance."""
        name = extractor.metadata.name
        self._extractors[name] = extractor
        return extractor

    def get_extractor(self, name: str) -> Optional[BaseFeatureExtractor]:
        return self._extractors.get(name)

    def list_extractors(self, category: Optional[FeatureCategory] = None) -> List[BaseFeatureExtractor]:
        if category:
            return [e for e in self._extractors.values() if e.metadata.category == category]
        return list(self._extractors.values())

    def compute_all(self, context: FeatureContext, feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Computes requested features (or all registered features) for the given context.
        Concatenates all resulting feature columns aligned by index.
        """
        extractors_to_run = (
            [self._extractors[n] for n in feature_names if n in self._extractors]
            if feature_names
            else list(self._extractors.values())
        )

        feature_dfs: List[pd.DataFrame] = []
        for extractor in extractors_to_run:
            try:
                res_df = extractor.compute(context)
                if res_df is not None and not res_df.empty:
                    feature_dfs.append(res_df)
            except Exception:
                continue

        if not feature_dfs:
            return pd.DataFrame()

        # Concatenate horizontally on index
        combined = pd.concat(feature_dfs, axis=1)
        # Drop duplicate column names if any
        combined = combined.loc[:, ~combined.columns.duplicated()]
        return combined


# Global registry singleton
feature_registry = FeatureRegistry()
