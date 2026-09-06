"""
StockSense AI — API v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, analyze, market, watchlist, portfolio, settings, data, ml, auth, backtesting, admin

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Biometric Face Authentication"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Panel & System Management"])
api_router.include_router(market.router, prefix="/market", tags=["Market Live Context"])
api_router.include_router(data.router, prefix="", tags=["Canonical Multi-Market Data"])
api_router.include_router(data.router, prefix="/data", tags=["Canonical Data Management"])
api_router.include_router(ml.router, prefix="", tags=["Machine Learning & Predictions"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(backtesting.router, prefix="/backtests", tags=["Backtesting & Quantitative Research"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["Backtesting & Quantitative Research"])

