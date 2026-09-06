"""Complete Initial Schema Creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-26 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create all 8 PostgreSQL schemas
    schemas = [
        "market_data", "fundamentals", "analysis",
        "portfolio", "ml", "news", "macro", "audit"
    ]
    for s in schemas:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {s};")

    # 2. Create Base Tables via Metadata Reflection/Creation
    from app.db.base import Base
    import app.models  # Load all 32 models
    
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.db.base import Base
    import app.models
    
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    
    schemas = [
        "market_data", "fundamentals", "analysis",
        "portfolio", "ml", "news", "macro", "audit"
    ]
    for s in schemas:
        op.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
