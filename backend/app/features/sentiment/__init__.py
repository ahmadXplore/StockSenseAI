"""
StockSense AI — Sentiment Features Package
"""

from app.features.sentiment.news_sentiment import NewsSentimentFeatureExtractor, news_sentiment_extractor

__all__ = ["NewsSentimentFeatureExtractor", "news_sentiment_extractor"]
