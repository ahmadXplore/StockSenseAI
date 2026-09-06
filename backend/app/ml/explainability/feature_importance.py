"""
StockSense AI — Explainability & Feature Importance Engine
Extracts driver signals, permutation importances, and factor attribution.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.inspection import permutation_importance


class ExplainabilityEngine:
    """
    Generates transparent feature attribution and rank explanations for predictions.
    """

    def compute_permutation_importance(
        self,
        model: Any,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        n_repeats: int = 5,
        random_state: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Computes model-agnostic permutation feature importance.
        """
        if X_val.empty or len(X_val) < 10:
            return []

        # If model is wrapper with _model attribute
        raw_m = getattr(model, "_model", model)
        scaler = getattr(model, "scaler", None)

        X_clean = X_val.fillna(0.0).values
        if scaler:
            X_clean = scaler.transform(X_clean)

        try:
            res = permutation_importance(
                raw_m, X_clean, y_val.values,
                n_repeats=n_repeats, random_state=random_state, n_jobs=-1
            )
            importances = []
            for i, col in enumerate(X_val.columns):
                mean_imp = float(res.importances_mean[i])
                std_imp = float(res.importances_std[i])
                importances.append({
                    "feature": col,
                    "importance_mean": round(mean_imp, 6),
                    "importance_std": round(std_imp, 6),
                    "rank": 0
                })

            # Sort and assign ranks
            importances.sort(key=lambda x: x["importance_mean"], reverse=True)
            for idx, item in enumerate(importances):
                item["rank"] = idx + 1

            return importances
        except Exception:
            return []

    def extract_prediction_drivers(
        self,
        feature_row: pd.Series,
        importances: Dict[str, float]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Explains an individual prediction by categorizing influential drivers.
        """
        sorted_feats = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        top_positive = []
        top_negative = []

        for name, score in sorted_feats[:8]:
            val = float(feature_row.get(name, 0.0)) if name in feature_row else 0.0
            driver_info = {
                "feature": name,
                "importance_score": round(score, 4),
                "feature_value": round(val, 4)
            }
            if score > 0.05:
                top_positive.append(driver_info)
            else:
                top_negative.append(driver_info)

        return {
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "all_ranked_features": [{"feature": k, "score": round(v, 4)} for k, v in sorted_feats]
        }


explainability_engine = ExplainabilityEngine()
