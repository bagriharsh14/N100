import os
import sqlite3
import pytest
from src.etl.loader import DB_PATH


def test_db_file_exists():
    assert os.path.exists(DB_PATH)


def test_companies_count_in_db():
    with sqlite3.connect(DB_PATH) as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    assert cnt == 92


def test_foreign_key_integrity():
    with sqlite3.connect(DB_PATH) as conn:
        orphans = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert len(orphans) == 0


def test_time_series_tables_populated():
    tables = ["profitandloss", "balancesheet", "cashflow", "stock_prices", "market_cap", "financial_ratios"]
    with sqlite3.connect(DB_PATH) as conn:
        for t in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            assert cnt > 500, f"Table {t} has too few rows: {cnt}"


def test_load_audit_file():
    assert os.path.exists("output/load_audit.csv")


def test_validation_failures_file():
    assert os.path.exists("output/validation_failures.csv")
