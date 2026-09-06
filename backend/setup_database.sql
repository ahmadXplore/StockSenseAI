-- ==============================================================================
-- StockSense AI — Complete PostgreSQL & TimescaleDB Database Setup Script
-- Open and run this in DBeaver (or pgAdmin / psql) connected to localhost:5432
-- ==============================================================================

-- 1. Create Role & Database (Run as postgres superuser)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'stocksense') THEN
        CREATE ROLE stocksense WITH LOGIN PASSWORD 'stocksense_dev_password' SUPERUSER;
    END IF;
END
$$;

-- Create Database if not exists
SELECT 'CREATE DATABASE stocksense OWNER stocksense'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stocksense')\gexec

-- ==============================================================================
-- Connect to the 'stocksense' database before running the commands below:
-- ==============================================================================
\c stocksense

-- 2. Enable TimescaleDB extension (if installed)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 3. Create all 8 Architecture Schemas
CREATE SCHEMA IF NOT EXISTS market_data AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS fundamentals AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS analysis AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS portfolio AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS ml AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS news AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS macro AUTHORIZATION stocksense;
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION stocksense;

-- Grant all permissions on schemas
GRANT ALL ON SCHEMA market_data TO stocksense;
GRANT ALL ON SCHEMA fundamentals TO stocksense;
GRANT ALL ON SCHEMA analysis TO stocksense;
GRANT ALL ON SCHEMA portfolio TO stocksense;
GRANT ALL ON SCHEMA ml TO stocksense;
GRANT ALL ON SCHEMA news TO stocksense;
GRANT ALL ON SCHEMA macro TO stocksense;
GRANT ALL ON SCHEMA audit TO stocksense;
