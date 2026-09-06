"""
StockSense AI — Chronological Event Loop & Timeline Stepper
Advances historical time strictly bar-by-bar, preventing look-ahead bias and synchronizing trading calendars.
"""

from typing import List, Dict, Any, Generator, Tuple, Optional


class MarketTimelineBar:
    def __init__(
        self,
        date_str: Optional[str] = None,
        prices_by_security: Optional[Dict[str, Dict[str, float]]] = None,
        features_by_security: Optional[Dict[str, Dict[str, Any]]] = None,
        predictions_by_security: Optional[Dict[str, Dict[str, Any]]] = None,
        corporate_actions: Optional[List[Dict[str, Any]]] = None,
        benchmark_bar: Optional[Dict[str, float]] = None,
        date: Optional[str] = None,
        prices: Optional[Dict[str, Dict[str, float]]] = None,
        features: Optional[Dict[str, Dict[str, Any]]] = None,
        predictions: Optional[Dict[str, Dict[str, Any]]] = None,
        benchmark: Optional[Dict[str, float]] = None,
    ):
        self.date = date or date_str or ""
        self.prices = prices or prices_by_security or {}
        self.features = features or features_by_security or {}
        self.predictions = predictions or predictions_by_security or {}
        self.corporate_actions = corporate_actions or []
        self.benchmark = benchmark or benchmark_bar or {}


class EventLoop:
    def __init__(self, timeline: List[MarketTimelineBar]):
        self.timeline = timeline
        self.current_idx = -1

    def __len__(self) -> int:
        return len(self.timeline)

    def iterate_bars(self) -> Generator[Tuple[int, MarketTimelineBar], None, None]:
        """
        Yields chronological bars one-by-one.
        At index i, historical decisions may ONLY reference bars <= i.
        """
        for idx, bar in enumerate(self.timeline):
            self.current_idx = idx
            yield idx, bar

    def get_current_date(self) -> Optional[str]:
        if 0 <= self.current_idx < len(self.timeline):
            return self.timeline[self.current_idx].date
        return None
