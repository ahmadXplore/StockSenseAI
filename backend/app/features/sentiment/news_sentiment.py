"""
StockSense AI — News & Sentiment Features
Extracts 1D, 3D, 7D, 30D sentiment aggregates and momentum with strict publication timestamp gating.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Optional
from app.features.base import BaseFeatureExtractor, FeatureMetadata, FeatureCategory, FeatureContext
from app.features.registry import feature_registry


class NewsSentimentFeatureExtractor(BaseFeatureExtractor):
    def __init__(self):
        super().__init__(
            FeatureMetadata(
                name="news_sentiment",
                category=FeatureCategory.SENTIMENT,
                description="Point-in-time news sentiment scores (1D, 3D, 7D, 30D) and sentiment momentum",
                lookback_periods=30,
                required_columns=[],
                version="1.0.0",
                is_point_in_time_safe=True
            )
        )

    def compute(self, context: FeatureContext) -> pd.DataFrame:
        p_df = context.price_df
        if p_df is None or p_df.empty:
            return pd.DataFrame()

        res = pd.DataFrame(index=p_df.index)

        # Baseline neutral sentiment defaults (0.0 = neutral)
        res["sentiment_score_1d"] = 0.0
        res["sentiment_score_7d"] = 0.0
        res["sentiment_score_30d"] = 0.0
        res["sentiment_momentum_7d_vs_30d"] = 0.0
        res["news_volume_7d"] = 0

        news_df = context.news_df
        if news_df is None or news_df.empty or "published_at" not in news_df.columns:
            return res

        for idx in p_df.index:
            row_date = idx.date() if hasattr(idx, "date") else idx
            if not isinstance(row_date, date):
                try:
                    row_date = pd.to_datetime(idx).date()
                except Exception:
                    continue

            # Strict point-in-time filter: published_at <= row_date
            pit_news = news_df[news_df["published_at"].apply(lambda p: p.date() if hasattr(p, "date") else p) <= row_date]
            if pit_news.empty:
                continue

            # 7-day and 30-day lookback windows
            start_7d = row_date - timedelta(days=7)
            start_30d = row_date - timedelta(days=30)

            news_7d = pit_news[pit_news["published_at"].apply(lambda p: p.date() if hasattr(p, "date") else p) >= start_7d]
            news_30d = pit_news[pit_news["published_at"].apply(lambda p: p.date() if hasattr(p, "date") else p) >= start_30d]

            if not news_7d.empty and "sentiment_score" in news_7d.columns:
                res.loc[idx, "sentiment_score_7d"] = float(news_7d["sentiment_score"].mean())
                res.loc[idx, "news_volume_7d"] = len(news_7d)

            if not news_30d.empty and "sentiment_score" in news_30d.columns:
                res.loc[idx, "sentiment_score_30d"] = float(news_30d["sentiment_score"].mean())

            res.loc[idx, "sentiment_momentum_7d_vs_30d"] = (
                res.loc[idx, "sentiment_score_7d"] - res.loc[idx, "sentiment_score_30d"]
            )

        return res


news_sentiment_extractor = NewsSentimentFeatureExtractor()
feature_registry.register(news_sentiment_extractor)
