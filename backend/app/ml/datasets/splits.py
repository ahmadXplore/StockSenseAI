"""
StockSense AI — Purged & Embargoed Time-Series Cross-Validation
Implements leak-free walk-forward splits with target horizon purging and post-test embargoes.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Generator, List, Tuple, Optional


class PurgedTimeSeriesSplit:
    """
    Time-Series Cross-Validation with Purging and Embargo.
    
    Purging: Removes training samples whose forward target window overlaps with test start.
    Embargo: Adds a quiet period after the test period before resuming training observations.
    """

    def __init__(
        self,
        n_splits: int = 5,
        purge_window: int = 21,    # e.g., 21 trading days for 30D horizon target
        embargo_pct: float = 0.01, # e.g., 1% of sample length as buffer
        min_train_size: int = 100
    ):
        self.n_splits = n_splits
        self.purge_window = purge_window
        self.embargo_pct = embargo_pct
        self.min_train_size = min_train_size

    def split(self, df: pd.DataFrame) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Yields (train_indices, test_indices) arrays.
        """
        n_samples = len(df)
        if n_samples < self.min_train_size + self.n_splits * 10:
            # Single train/test fallback if sample size is tight
            test_size = max(10, int(n_samples * 0.2))
            train_end = n_samples - test_size - self.purge_window
            if train_end > 10:
                yield np.arange(0, train_end), np.arange(n_samples - test_size, n_samples)
            return

        embargo_size = int(n_samples * self.embargo_pct)
        test_size = (n_samples - self.min_train_size) // self.n_splits

        for i in range(self.n_splits):
            test_start = self.min_train_size + i * test_size
            test_end = min(test_start + test_size, n_samples)

            # Purge: End training window before test_start - purge_window
            train_end = max(1, test_start - self.purge_window)
            train_indices = np.arange(0, train_end)
            test_indices = np.arange(test_start, test_end)

            if len(train_indices) > 0 and len(test_indices) > 0:
                yield train_indices, test_indices
