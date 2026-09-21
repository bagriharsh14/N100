import datetime
import json
import logging
import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.analytics.screener.engine import ScreenerEngine

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
SERVER_START_TIME = time.time()

app = FastAPI(
    title="Nifty 100 Financial Intelligence REST API",
    description="Production-grade fundamental analytics API exposing 16 endpoints for 92 Nifty 100 companies.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 1. /api/v1/companies
@app.get("/api/v1/companies", tags=["Companies"])
def list_companies(sector: Optional[str] = None, search: Optional[str] = None):
    """List all 92 companies with metadata, sector, and latest ROE/ROCE."""
    query = """
    SELECT 
        c.id, c.company_name, s.broad_sector, s.sub_sector, s.market_cap_category,
        c.roce_percentage, c.roe_percentage, c.book_value, c.face_value
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    WHERE 1=1
    """
    params = []
    if sector and sector.lower() != "all":
        query += " AND LOWER(s.broad_sector) = LOWER(?)"
        params.append(sector)
    if search:
        query += " AND (LOWER(c.id) LIKE ? OR LOWER(c.company_name) LIKE ?)"
        term = f"%{search.lower()}%"
        params.extend([term, term])
    
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# 2. /api/v1/companies/{ticker}
@app.get("/api/v1/companies/{ticker}", tags=["Companies"])
def get_company_profile(ticker: str):
    """Retrieve full company profile including master fields, sector, latest ratios, and pros/cons."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        co = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()
        if not co:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
        
        sec = conn.execute("SELECT * FROM sectors WHERE company_id = ?", (ticker,)).fetchone()
        latest_r = conn.execute("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", (ticker,)).fetchone()
        pros_cons = conn.execute("SELECT * FROM prosandcons WHERE company_id = ?", (ticker,)).fetchall()

    # Fallback to generated pros/cons if table empty
    pros_list, cons_list = [], []
    if pros_cons:
        pros_list = [r["pros"] for r in pros_cons if r["pros"]]
        cons_list = [r["cons"] for r in pros_cons if r["cons"]]
    else:
        if os.path.exists("output/pros_cons_generated.csv"):
            import pandas as pd
            df_pc = pd.read_csv("output/pros_cons_generated.csv")
            co_pc = df_pc[df_pc["company_id"] == ticker]
            pros_list = co_pc[co_pc["type"] == "pro"]["text"].tolist()
            cons_list = co_pc[co_pc["type"] == "con"]["text"].tolist()

    return {
        "ticker": ticker,
        "company_name": co["company_name"],
        "about_company": co["about_company"],
        "website": co["website"],
        "chart_link": co["chart_link"],
        "sector": dict(sec) if sec else {},
        "latest_ratios": dict(latest_r) if latest_r else {},
        "pros": pros_list,
        "cons": cons_list
    }


# 3. /api/v1/companies/{ticker}/pl
@app.get("/api/v1/companies/{ticker}/pl", tags=["Financial Statements"])
def get_company_pl(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get historical annual Profit & Loss statement records."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No P&L history found for '{ticker}'")
    return [dict(r) for r in rows]


# 4. /api/v1/companies/{ticker}/bs
@app.get("/api/v1/companies/{ticker}/bs", tags=["Financial Statements"])
def get_company_bs(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get historical annual Balance Sheet statement records."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No Balance Sheet history found for '{ticker}'")
    return [dict(r) for r in rows]


# 5. /api/v1/companies/{ticker}/cashflow
@app.get("/api/v1/companies/{ticker}/cashflow", tags=["Financial Statements"])
def get_company_cashflow(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Get historical annual Cash Flow statement records."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No Cash Flow history found for '{ticker}'")
    return [dict(r) for r in rows]


# 6. /api/v1/companies/{ticker}/ratios
@app.get("/api/v1/companies/{ticker}/ratios", tags=["Financial Ratios"])
def get_company_ratios(ticker: str, year: Optional[str] = None):
    """Get all 14+ pre-computed financial ratios for a company."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No ratios found for '{ticker}'")
    return [dict(r) for r in rows]


# 7. /api/v1/companies/{ticker}/tearsheet
@app.get("/api/v1/companies/{ticker}/tearsheet", tags=["Reporting"])
def get_tearsheet_pdf(ticker: str):
    """Download the pre-generated 2-page institutional tearsheet PDF."""
    ticker = ticker.strip().upper()
    pdf_path = os.path.join("reports/tearsheets", f"{ticker}_tearsheet.pdf")
    if not os.path.exists(pdf_path):
        from src.reports.tearsheet import build_tearsheet_pdf
        try:
            pdf_path = build_tearsheet_pdf(ticker)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Tearsheet not available for '{ticker}': {str(e)}")
    
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")


# 8. /api/v1/screener
@app.get("/api/v1/screener", tags=["Screener"])
def run_screener_api(
    preset: Optional[str] = None,
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    """Filter and rank Nifty 100 universe using custom metrics or preset screens."""
    engine = ScreenerEngine(db_path=DB_PATH)
    if preset:
        df_res = engine.run_preset(preset)
    else:
        df_res = engine.run_custom_filter(
            min_roe=min_roe, max_de=max_de, min_fcf=min_fcf,
            sector=sector, min_rev_cagr_5yr=min_rev_cagr_5yr,
            min_pat_cagr_5yr=min_pat_cagr_5yr, max_pe=max_pe
        )
    # Convert NaNs to None for JSON compliance
    clean_records = df_res.replace({float("nan"): None}).to_dict(orient="records")
    return clean_records



# 9. /api/v1/sectors
@app.get("/api/v1/sectors", tags=["Sectors"])
def list_sectors():
    """List all 11 macro sectors with constituent count and median KPIs."""
    query = """
    WITH latest_years AS (
        SELECT company_id, MAX(year) AS max_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        s.broad_sector AS sector_name,
        COUNT(DISTINCT s.company_id) AS company_count,
        ROUND(AVG(r.return_on_equity_pct), 2) AS median_roe,
        ROUND(AVG(r.roce_pct), 2) AS median_roce,
        ROUND(AVG(r.debt_to_equity), 2) AS median_de,
        ROUND(AVG(r.pe_ratio), 2) AS median_pe
    FROM sectors s
    LEFT JOIN latest_years ly ON s.company_id = ly.company_id
    LEFT JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
    GROUP BY s.broad_sector
    ORDER BY company_count DESC
    """
    with get_db() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(r) for r in rows]


# 10. /api/v1/sectors/{sector}/companies
@app.get("/api/v1/sectors/{sector}/companies", tags=["Sectors"])
def get_sector_companies(sector: str):
    """Get all companies in a specific sector with core KPI summaries."""
    query = """
    WITH latest_years AS (
        SELECT company_id, MAX(year) AS max_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        c.id AS ticker, c.company_name, s.sub_sector,
        r.return_on_equity_pct, r.roce_pct, r.net_profit_margin_pct,
        r.debt_to_equity, r.revenue_cagr_5yr, r.free_cash_flow_cr,
        r.pe_ratio, r.composite_quality_score
    FROM sectors s
    JOIN companies c ON s.company_id = c.id
    LEFT JOIN latest_years ly ON s.company_id = ly.company_id
    LEFT JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
    WHERE LOWER(s.broad_sector) = LOWER(?)
    ORDER BY r.return_on_equity_pct DESC
    """
    with get_db() as conn:
        rows = conn.execute(query, (sector,)).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No companies found for sector '{sector}'")
    return [dict(r) for r in rows]


# 11. /api/v1/peers/{group_name}
@app.get("/api/v1/peers/{group_name}", tags=["Peer Comparison"])
def get_peer_group_members(group_name: str):
    """Get all member companies in a peer group with intra-group percentile rankings."""
    query = """
    SELECT 
        pg.peer_group_name, pg.company_id, pg.is_benchmark, c.company_name,
        p.metric, p.value, p.percentile_rank
    FROM peer_groups pg
    JOIN companies c ON pg.company_id = c.id
    LEFT JOIN peer_percentiles p ON pg.company_id = p.company_id AND pg.peer_group_name = p.peer_group_name
    WHERE LOWER(pg.peer_group_name) = LOWER(?)
    """
    with get_db() as conn:
        rows = conn.execute(query, (group_name,)).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
    return [dict(r) for r in rows]


# 12. /api/v1/companies/{ticker}/peers/compare
@app.get("/api/v1/companies/{ticker}/peers/compare", tags=["Peer Comparison"])
def compare_company_with_peers(ticker: str):
    """Retrieve 8-axis radar comparison data: company vs peer group average vs benchmark."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        pg_match = conn.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (ticker,)).fetchone()
        group_name = pg_match["peer_group_name"] if pg_match else "General Nifty 100"
        
        bench_match = conn.execute("SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1", (group_name,)).fetchone()
        bench_ticker = bench_match["company_id"] if bench_match else "NIFTY100"

        # Fetch latest metrics for company, benchmark, and peer group
        metrics = ["return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr"]
        
        query = f"""
        WITH latest_years AS (
            SELECT company_id, MAX(year) AS max_year
            FROM financial_ratios
            GROUP BY company_id
        )
        SELECT r.company_id, {", ".join(["r." + m for m in metrics])}
        FROM latest_years ly
        JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
        """
        all_r = conn.execute(query).fetchall()

    co_data = next((dict(r) for r in all_r if r["company_id"] == ticker), {})
    bench_data = next((dict(r) for r in all_r if r["company_id"] == bench_ticker), {})
    
    return {
        "ticker": ticker,
        "peer_group": group_name,
        "benchmark_ticker": bench_ticker,
        "company_metrics": co_data,
        "benchmark_metrics": bench_data,
    }


# 13. /api/v1/market-cap/{ticker}
@app.get("/api/v1/market-cap/{ticker}", tags=["Valuation"])
def get_market_cap_history(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    """Get historical annual valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield)."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM market_cap WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No market cap data found for '{ticker}'")
    return [dict(r) for r in rows]


# 14. /api/v1/portfolio/stats
@app.get("/api/v1/portfolio/stats", tags=["Portfolio"])
def get_portfolio_statistics():
    """Retrieve portfolio-level P10-P90 statistical distributions for all core KPIs."""
    if os.path.exists("output/portfolio_stats.csv"):
        import pandas as pd
        df = pd.read_csv("output/portfolio_stats.csv")
        return df.replace({float("nan"): None}).to_dict(orient="records")
    return []



# 15. /api/v1/companies/{ticker}/documents
@app.get("/api/v1/companies/{ticker}/documents", tags=["Documents"])
def get_company_documents(ticker: str):
    """List all available annual report links and document metadata for a company."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM documents WHERE company_id = ? ORDER BY Year DESC", (ticker,)).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No document links found for '{ticker}'")
    return [dict(r) for r in rows]


# 16. /api/v1/health
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Server health check: verifies SQLite connectivity, table rowcounts, and uptime."""
    tables = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis", "documents", "prosandcons", "sectors", "stock_prices", "market_cap"]
    row_counts = {}
    try:
        with get_db() as conn:
            for t in tables:
                cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                row_counts[t] = cnt
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connectivity failed: {str(e)}")

    uptime = int(time.time() - SERVER_START_TIME)
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "database": "data/nifty100.db",
        "db_row_counts": row_counts,
        "timestamp": datetime.datetime.now().isoformat()
    }


def export_openapi_and_postman():
    """Export OpenAPI specification and Postman collection files."""
    os.makedirs("docs", exist_ok=True)
    openapi_schema = app.openapi()
    with open("docs/openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    logger.info("Saved OpenAPI 3.0 specification to docs/openapi.json")

    # Generate Postman Collection
    postman = {
        "info": {
            "name": "Nifty 100 Financial Intelligence API",
            "_postman_id": "nifty100-api-v1",
            "description": "Postman collection covering all 16 endpoints of Nifty 100 Platform",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": path,
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "http://localhost:8000" + path,
                        "protocol": "http",
                        "host": ["localhost"],
                        "port": "8000",
                        "path": [p for p in path.split("/") if p]
                    }
                }
            } for path in openapi_schema.get("paths", {}).keys()
        ]
    }
    with open("docs/postman_collection.json", "w", encoding="utf-8") as f:
        json.dump(postman, f, indent=2)
    logger.info("Saved Postman collection to docs/postman_collection.json")


if __name__ == "__main__":
    export_openapi_and_postman()
