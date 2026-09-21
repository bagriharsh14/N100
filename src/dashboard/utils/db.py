import functools
import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")


@st.cache_data(ttl=600)
def query_db(query: str, params: tuple = ()) -> pd.DataFrame:
    """Execute SQL query with caching and return DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(query, conn, params=params)
    return df


@st.cache_data(ttl=600)
def get_all_companies() -> pd.DataFrame:
    """Get all 92 companies with sector mapping."""
    q = """
    SELECT 
        c.id, c.company_name, c.about_company, c.website, c.chart_link,
        s.broad_sector, s.sub_sector, s.market_cap_category
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    ORDER BY c.company_name
    """
    return query_db(q)


@st.cache_data(ttl=600)
def get_latest_financial_ratios() -> pd.DataFrame:
    """Fetch latest financial ratios for all companies."""
    q = """
    WITH latest_years AS (
        SELECT company_id, MAX(year) AS max_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        c.id AS ticker,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        r.*,
        p.sales,
        p.operating_profit,
        p.net_profit
    FROM latest_years ly
    JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
    JOIN companies c ON r.company_id = c.id
    LEFT JOIN sectors s ON r.company_id = s.company_id
    LEFT JOIN profitandloss p ON r.company_id = p.company_id AND r.year = p.year
    """
    return query_db(q)
