"""
StockSense AI — Pytest Fixtures & SQLite Dialect Compatibility Hooks
Allows PostgreSQL schemas, JSONB, ARRAY, UUID, INET to compile cleanly during SQLite unit testing.
"""

import pytest
import json
from sqlalchemy import event, Table
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID, INET

# Compile PostgreSQL ARRAY as TEXT on SQLite
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

# Compile PostgreSQL JSONB as TEXT/JSON on SQLite
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

# Compile PostgreSQL INET as TEXT on SQLite
@compiles(INET, "sqlite")
def compile_inet_sqlite(type_, compiler, **kw):
    return "TEXT"

# Compile PostgreSQL UUID as TEXT on SQLite
@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"


@event.listens_for(Table, "before_create")
def remove_schema_for_sqlite(target, connection, **kw):
    """Strip schema prefixes when testing against SQLite in-memory database."""
    if connection.dialect.name == "sqlite":
        target.schema = None
