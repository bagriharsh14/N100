import datetime
import logging
import os
import sqlite3
import sys
import time
from typing import Dict, List, Tuple
import pandas as pd
from dotenv import load_dotenv

# Ensure root directory is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import DataQualityValidator


load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
RAW_DIR = "data/raw"
SUPPORTING_DIR = "data/supporting"
OUTPUT_DIR = "output"


def init_db(db_path: str, schema_path: str = "src/etl/schema.sql") -> None:
    """Initialize database schema from SQL file."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    logger.info("Database schema initialized at %s", db_path)


def load_all_datasets(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load, validate, normalize, and insert all 12 datasets into SQLite."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start_time = time.time()
    validator = DataQualityValidator()
    audit_records: List[Dict] = []

    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. Companies (Core)
        t0 = time.time()
        co_path = os.path.join(RAW_DIR, "companies.xlsx")
        df_co_raw = pd.read_excel(co_path, header=1)
        rows_in = len(df_co_raw)
        df_co = df_co_raw.copy()
        df_co["id"] = df_co["id"].apply(normalize_ticker)
        if "company_name" in df_co.columns:
            df_co["company_name"] = df_co["company_name"].astype(str).str.strip().str.replace("\n", " ", regex=False)
        df_co = validator.validate_companies(df_co)
        valid_companies = set(df_co["id"].unique())

        df_co.to_sql("companies", conn, if_exists="replace", index=False)
        rows_out = len(df_co)
        audit_records.append({
            "table": "companies",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 2. Profit and Loss (Core)
        t0 = time.time()
        pl_path = os.path.join(RAW_DIR, "profitandloss.xlsx")
        df_pl_raw = pd.read_excel(pl_path, header=1)
        rows_in = len(df_pl_raw)
        df_pl = df_pl_raw.copy()
        df_pl["company_id"] = df_pl["company_id"].apply(normalize_ticker)
        df_pl["year"] = df_pl["year"].apply(normalize_year)
        df_pl = validator.validate_pl(df_pl, valid_companies)
        df_pl.to_sql("profitandloss", conn, if_exists="replace", index=False)
        rows_out = len(df_pl)
        audit_records.append({
            "table": "profitandloss",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 3. Balance Sheet (Core)
        t0 = time.time()
        bs_path = os.path.join(RAW_DIR, "balancesheet.xlsx")
        df_bs_raw = pd.read_excel(bs_path, header=1)
        rows_in = len(df_bs_raw)
        df_bs = df_bs_raw.copy()
        df_bs["company_id"] = df_bs["company_id"].apply(normalize_ticker)
        df_bs["year"] = df_bs["year"].apply(normalize_year)
        df_bs = validator.validate_bs(df_bs, valid_companies)
        df_bs.to_sql("balancesheet", conn, if_exists="replace", index=False)
        rows_out = len(df_bs)
        audit_records.append({
            "table": "balancesheet",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 4. Cash Flow (Core)
        t0 = time.time()
        cf_path = os.path.join(RAW_DIR, "cashflow.xlsx")
        df_cf_raw = pd.read_excel(cf_path, header=1)
        rows_in = len(df_cf_raw)
        df_cf = df_cf_raw.copy()
        df_cf["company_id"] = df_cf["company_id"].apply(normalize_ticker)
        df_cf["year"] = df_cf["year"].apply(normalize_year)
        df_cf = validator.validate_cf(df_cf, valid_companies)
        df_cf.to_sql("cashflow", conn, if_exists="replace", index=False)
        rows_out = len(df_cf)
        audit_records.append({
            "table": "cashflow",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 5. Analysis (Core)
        t0 = time.time()
        an_path = os.path.join(RAW_DIR, "analysis.xlsx")
        df_an_raw = pd.read_excel(an_path, header=1)
        rows_in = len(df_an_raw)
        df_an = df_an_raw.copy()
        df_an["company_id"] = df_an["company_id"].apply(normalize_ticker)
        df_an = df_an[df_an["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id"], keep="last")
        df_an.to_sql("analysis", conn, if_exists="replace", index=False)
        rows_out = len(df_an)
        audit_records.append({
            "table": "analysis",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 6. Documents (Core)
        t0 = time.time()
        doc_path = os.path.join(RAW_DIR, "documents.xlsx")
        df_doc_raw = pd.read_excel(doc_path, header=1)
        rows_in = len(df_doc_raw)
        df_doc = df_doc_raw.copy()
        df_doc["company_id"] = df_doc["company_id"].apply(normalize_ticker)
        if "Year" in df_doc.columns:
            df_doc["Year"] = pd.to_numeric(df_doc["Year"], errors="coerce").fillna(0).astype(int)
        df_doc = df_doc[df_doc["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id", "Year"], keep="last")
        if "is_url_valid" not in df_doc.columns:
            df_doc["is_url_valid"] = 1
        df_doc.to_sql("documents", conn, if_exists="replace", index=False)
        rows_out = len(df_doc)
        audit_records.append({
            "table": "documents",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 7. Pros and Cons (Core)
        t0 = time.time()
        pc_path = os.path.join(RAW_DIR, "prosandcons.xlsx")
        df_pc_raw = pd.read_excel(pc_path, header=1)
        rows_in = len(df_pc_raw)
        df_pc = df_pc_raw.copy()
        df_pc["company_id"] = df_pc["company_id"].apply(normalize_ticker)
        df_pc = df_pc[df_pc["company_id"].isin(valid_companies)]
        df_pc.to_sql("prosandcons", conn, if_exists="replace", index=False)
        rows_out = len(df_pc)
        audit_records.append({
            "table": "prosandcons",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 8. Sectors (Supplementary)
        t0 = time.time()
        sec_path = os.path.join(SUPPORTING_DIR, "sectors.xlsx")
        df_sec_raw = pd.read_excel(sec_path, header=0)
        rows_in = len(df_sec_raw)
        df_sec = df_sec_raw.copy()
        df_sec["company_id"] = df_sec["company_id"].apply(normalize_ticker)
        if "id" in df_sec.columns:
            df_sec = df_sec.drop(columns=["id"])
        df_sec = df_sec[df_sec["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id"], keep="last")
        df_sec.to_sql("sectors", conn, if_exists="replace", index=False)
        rows_out = len(df_sec)
        audit_records.append({
            "table": "sectors",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 9. Stock Prices (Supplementary)
        t0 = time.time()
        sp_path = os.path.join(SUPPORTING_DIR, "stock_prices.xlsx")
        df_sp_raw = pd.read_excel(sp_path, header=0)
        rows_in = len(df_sp_raw)
        df_sp = df_sp_raw.copy()
        df_sp["company_id"] = df_sp["company_id"].apply(normalize_ticker)
        df_sp["date"] = df_sp["date"].astype(str).str.split("T").str[0].str.strip()
        if "id" in df_sp.columns:
            df_sp = df_sp.drop(columns=["id"])
        df_sp = df_sp[df_sp["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id", "date"], keep="last")
        df_sp.to_sql("stock_prices", conn, if_exists="replace", index=False)
        rows_out = len(df_sp)
        audit_records.append({
            "table": "stock_prices",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 10. Market Cap (Supplementary)
        t0 = time.time()
        mc_path = os.path.join(SUPPORTING_DIR, "market_cap.xlsx")
        df_mc_raw = pd.read_excel(mc_path, header=0)
        rows_in = len(df_mc_raw)
        df_mc = df_mc_raw.copy()
        df_mc["company_id"] = df_mc["company_id"].apply(normalize_ticker)
        if "id" in df_mc.columns:
            df_mc = df_mc.drop(columns=["id"])
        df_mc["year"] = pd.to_numeric(df_mc["year"], errors="coerce").astype(int)
        df_mc = df_mc[df_mc["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id", "year"], keep="last")
        df_mc.to_sql("market_cap", conn, if_exists="replace", index=False)
        rows_out = len(df_mc)
        audit_records.append({
            "table": "market_cap",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 11. Peer Groups (Supplementary)
        t0 = time.time()
        pg_path = os.path.join(SUPPORTING_DIR, "peer_groups.xlsx")
        df_pg_raw = pd.read_excel(pg_path, header=0)
        rows_in = len(df_pg_raw)
        df_pg = df_pg_raw.copy()
        df_pg["company_id"] = df_pg["company_id"].apply(normalize_ticker)
        if "id" in df_pg.columns:
            df_pg = df_pg.drop(columns=["id"])
        df_pg = df_pg[df_pg["company_id"].isin(valid_companies)]
        df_pg.to_sql("peer_groups", conn, if_exists="replace", index=False)
        rows_out = len(df_pg)
        audit_records.append({
            "table": "peer_groups",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rejected": rows_in - rows_out,
            "timestamp": datetime.datetime.now().isoformat(),
            "runtime_s": round(time.time() - t0, 3)
        })

        # 12. Pre-computed Financial Ratios (Supplementary baseline if present)
        t0 = time.time()
        fr_path = os.path.join(SUPPORTING_DIR, "financial_ratios.xlsx")
        if os.path.exists(fr_path):
            df_fr_raw = pd.read_excel(fr_path, header=0)
            rows_in = len(df_fr_raw)
            df_fr = df_fr_raw.copy()
            df_fr["company_id"] = df_fr["company_id"].apply(normalize_ticker)
            df_fr["year"] = df_fr["year"].apply(normalize_year)
            if "id" in df_fr.columns:
                df_fr = df_fr.drop(columns=["id"])
            df_fr = df_fr[df_fr["company_id"].isin(valid_companies)].drop_duplicates(subset=["company_id", "year"], keep="last")
            df_fr.to_sql("financial_ratios", conn, if_exists="replace", index=False)
            rows_out = len(df_fr)
            audit_records.append({
                "table": "financial_ratios (seed)",
                "rows_in": rows_in,
                "rows_out": rows_out,
                "rejected": rows_in - rows_out,
                "timestamp": datetime.datetime.now().isoformat(),
                "runtime_s": round(time.time() - t0, 3)
            })

        # Multi-year coverage check (DQ-16)
        validator.validate_coverage(df_pl, valid_companies)

    # Export load audit CSV
    audit_df = pd.DataFrame(audit_records)
    audit_df.to_csv(os.path.join(OUTPUT_DIR, "load_audit.csv"), index=False)
    logger.info("Saved load audit to %s/load_audit.csv", OUTPUT_DIR)

    # Export validation failures
    validator.export_failures_csv(os.path.join(OUTPUT_DIR, "validation_failures.csv"))

    logger.info("Completed full ETL load in %.2f seconds", time.time() - start_time)
    return audit_df, pd.DataFrame(validator.failures)


if __name__ == "__main__":
    load_all_datasets()
