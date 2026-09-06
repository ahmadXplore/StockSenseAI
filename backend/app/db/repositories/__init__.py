"""
StockSense AI — Repository Layer Registry
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.company_repo import CompanyRepository
from app.db.repositories.price_repo import PriceRepository
from app.db.repositories.technical_repo import TechnicalRepository
from app.db.repositories.fundamental_repo import FundamentalRepository
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.report_repo import ReportRepository
from app.db.repositories.portfolio_repo import PortfolioRepository
from app.db.repositories.alert_repo import AlertRepository
from app.db.repositories.macro_repo import MacroRepository
from app.db.repositories.news_repo import NewsRepository
from app.db.repositories.audit_repo import AuditRepository

__all__ = [
    "BaseRepository",
    "CompanyRepository",
    "PriceRepository",
    "TechnicalRepository",
    "FundamentalRepository",
    "JobRepository",
    "ReportRepository",
    "PortfolioRepository",
    "AlertRepository",
    "MacroRepository",
    "NewsRepository",
    "AuditRepository",
]
