"""
StockSense AI — SQLAlchemy Base Declarative Model
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, Table
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID, INET


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Compile PostgreSQL types for SQLite
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(INET, "sqlite")
def compile_inet_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"


from app.core.config import settings

# Strip schema prefixes for SQLite so all queries and DDL use unqualified table names
@event.listens_for(Table, "after_parent_attach")
def strip_schema_for_sqlite(target, parent):
    if "sqlite" in settings.database_url.lower():
        target.schema = None


