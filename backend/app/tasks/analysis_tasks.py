"""
StockSense AI — Celery Analysis Tasks
"""

from app.tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.run_full_analysis_job")
def run_full_analysis_job(self, ticker: str, investment_amount: float, risk_tolerance: str, horizons: list):
    """
    Celery background worker task for running full stock analysis pipeline.
    Progress is tracked in Redis.
    """
    logger.info("Starting background analysis job", ticker=ticker, task_id=self.request.id)
    # Background pipeline will execute in Phase 2/3
    return {"job_id": self.request.id, "ticker": ticker, "status": "PENDING"}
