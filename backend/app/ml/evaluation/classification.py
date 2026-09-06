"""
StockSense AI — Classification Evaluation Metrics
Calculates Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, and Confusion Matrix.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, balanced_accuracy_score, confusion_matrix
)


@dataclass
class ClassificationMetricsResult:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    balanced_accuracy: float
    confusion_matrix: Dict[str, int]


def evaluate_classification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray
) -> ClassificationMetricsResult:
    y_t = np.asarray(y_true).ravel().astype(int)
    y_p = np.asarray(y_pred).ravel().astype(int)
    y_pr = np.asarray(y_prob).ravel().astype(float)

    acc = float(accuracy_score(y_t, y_p) * 100.0)
    prec = float(precision_score(y_t, y_p, zero_division=0) * 100.0)
    rec = float(recall_score(y_t, y_p, zero_division=0) * 100.0)
    f1 = float(f1_score(y_t, y_p, zero_division=0) * 100.0)
    bal_acc = float(balanced_accuracy_score(y_t, y_p) * 100.0)

    try:
        auc = float(roc_auc_score(y_t, y_pr))
    except Exception:
        auc = 0.5

    cm = confusion_matrix(y_t, y_p)
    cm_dict = {
        "true_negatives": int(cm[0, 0]) if cm.shape == (2, 2) else 0,
        "false_positives": int(cm[0, 1]) if cm.shape == (2, 2) else 0,
        "false_negatives": int(cm[1, 0]) if cm.shape == (2, 2) else 0,
        "true_positives": int(cm[1, 1]) if cm.shape == (2, 2) else 0,
    }

    return ClassificationMetricsResult(
        accuracy=round(acc, 2),
        precision=round(prec, 2),
        recall=round(rec, 2),
        f1_score=round(f1, 2),
        roc_auc=round(auc, 4),
        balanced_accuracy=round(bal_acc, 2),
        confusion_matrix=cm_dict
    )
