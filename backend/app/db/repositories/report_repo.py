"""
StockSense AI — Analysis Report Repository
Handles atomic multi-table persistence across all 14 report sections.
"""

import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.repositories.base import BaseRepository
from app.models.analysis import (
    AnalysisReport, ScoreComponent, Prediction, Scenario, InvestmentCalculatorRun,
    FundamentalHealthScore, ValuationAnalysis, RiskMetrics, ExitStrategy, AnomalyDetection
)


class ReportRepository(BaseRepository[AnalysisReport]):
    def __init__(self, session: AsyncSession):
        super().__init__(AnalysisReport, session)

    async def get_latest_by_ticker(self, ticker: str) -> Optional[AnalysisReport]:
        """Fetch latest analysis report for ticker."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(AnalysisReport)
            .where(AnalysisReport.ticker == ticker_clean)
            .order_by(desc(AnalysisReport.generated_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_full_report_atomic(
        self,
        report_data: dict,
        predictions_data: List[dict],
        scenarios_data: List[dict],
        scores_data: List[dict],
        calculator_data: Optional[dict] = None,
        fundamental_health_data: Optional[dict] = None,
        valuation_data: Optional[dict] = None,
        risk_data: Optional[dict] = None,
        exit_data: Optional[dict] = None,
        anomaly_data: Optional[dict] = None,
    ) -> AnalysisReport:
        """
        Atomically persists an entire report and all 10 normalized section rows
        within a single database transaction.
        """
        # Create master report row
        report = AnalysisReport(**report_data)
        self.session.add(report)
        await self.session.flush() # Populate report.id

        # Relational child items
        for p in predictions_data:
            self.session.add(Prediction(report_id=report.id, **p))

        for s in scenarios_data:
            self.session.add(Scenario(report_id=report.id, **s))

        for sc in scores_data:
            self.session.add(ScoreComponent(report_id=report.id, **sc))

        if calculator_data:
            self.session.add(InvestmentCalculatorRun(report_id=report.id, **calculator_data))

        if fundamental_health_data:
            self.session.add(FundamentalHealthScore(report_id=report.id, **fundamental_health_data))

        if valuation_data:
            self.session.add(ValuationAnalysis(report_id=report.id, **valuation_data))

        if risk_data:
            self.session.add(RiskMetrics(report_id=report.id, **risk_data))

        if exit_data:
            self.session.add(ExitStrategy(report_id=report.id, **exit_data))

        if anomaly_data:
            self.session.add(AnomalyDetection(report_id=report.id, **anomaly_data))

        await self.session.flush()
        return report
