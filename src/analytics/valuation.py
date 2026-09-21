import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"


class ValuationAnalytics:
    """Computes valuation multiples, sector relative benchmarks, and overvaluation flags."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize valuation analytics."""
        self.db_path = db_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def compute_valuation_summary(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Compute valuation summaries for all 92 companies and flag caution/discount."""
        with sqlite3.connect(self.db_path) as conn:
            df_co = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
            df_sec = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
            df_mc = pd.read_sql("SELECT * FROM market_cap ORDER BY company_id, year", conn)
            
            query = """
            WITH latest_years AS (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            )
            SELECT r.* FROM latest_years ly
            JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
            """
            df_latest_r = pd.read_sql(query, conn)

        # Merge base info
        df_base = pd.merge(df_co, df_sec, on="company_id", how="left")
        df_base = pd.merge(df_base, df_latest_r, on="company_id", how="left")

        # Compute 5-year historical medians from market_cap
        mc_5yr_medians = df_mc.groupby("company_id").agg({
            "pe_ratio": "median",
            "pb_ratio": "median",
            "ev_ebitda": "median",
            "dividend_yield_pct": "median",
            "market_cap_crore": "last",
            "enterprise_value_crore": "last",
        }).reset_index().rename(columns={
            "pe_ratio": "pe_5yr_median",
            "pb_ratio": "pb_5yr_median",
            "ev_ebitda": "ev_ebitda_5yr_median",
            "dividend_yield_pct": "div_yield_5yr_median"
        })

        summary = pd.merge(df_base, mc_5yr_medians, on="company_id", how="left")

        # Sector median P/E and EV/EBITDA
        sec_medians = summary.groupby("broad_sector")["pe_ratio"].median().to_dict()
        sec_ev_medians = summary.groupby("broad_sector")["ev_ebitda"].median().to_dict()

        summary["sector_pe_median"] = summary["broad_sector"].map(sec_medians)
        summary["sector_ev_median"] = summary["broad_sector"].map(sec_ev_medians)

        flags: List[Dict[str, Any]] = []
        valuation_badges = []

        for _, row in summary.iterrows():
            cid = row["company_id"]
            sec = row.get("broad_sector", "General")
            pe = row.get("pe_ratio")
            sec_pe = row.get("sector_pe_median")
            badge = "Fair"

            if pd.notna(pe) and pd.notna(sec_pe) and sec_pe > 0:
                if pe > (sec_pe * 1.5):
                    badge = "Caution (Premium)"
                    flags.append({
                        "company_id": cid,
                        "company_name": row.get("company_name"),
                        "sector": sec,
                        "metric": "P/E Ratio",
                        "value": pe,
                        "sector_median": sec_pe,
                        "flag": "Caution",
                        "rationale": f"Trading at {pe:.1f}x P/E, >1.5x sector median of {sec_pe:.1f}x (SIMULATED)",
                    })
                elif pe < (sec_pe * 0.7) and pe > 0:
                    badge = "Discount (Value)"
                    flags.append({
                        "company_id": cid,
                        "company_name": row.get("company_name"),
                        "sector": sec,
                        "metric": "P/E Ratio",
                        "value": pe,
                        "sector_median": sec_pe,
                        "flag": "Discount",
                        "rationale": f"Trading at {pe:.1f}x P/E, <0.7x sector median of {sec_pe:.1f}x (SIMULATED)",
                    })

            valuation_badges.append(badge)

        summary["valuation_badge"] = valuation_badges

        # Export Deliverable D-12: valuation_summary.xlsx
        cols_summary = [
            "company_id", "company_name", "broad_sector", "sub_sector",
            "pe_ratio", "pe_5yr_median", "sector_pe_median",
            "pb_ratio", "pb_5yr_median",
            "ev_ebitda", "ev_ebitda_5yr_median", "sector_ev_median",
            "dividend_yield_pct", "fcf_yield_pct", "valuation_badge"
        ]
        available_cols = [c for c in cols_summary if c in summary.columns]
        summary[available_cols].to_excel(os.path.join(OUTPUT_DIR, "valuation_summary.xlsx"), index=False)
        logger.info("Saved valuation summary for 92 companies to %s/valuation_summary.xlsx", OUTPUT_DIR)

        # Export valuation flags CSV
        df_flags = pd.DataFrame(flags)
        df_flags.to_csv(os.path.join(OUTPUT_DIR, "valuation_flags.csv"), index=False)
        logger.info("Saved %d valuation flags to %s/valuation_flags.csv", len(df_flags), OUTPUT_DIR)

        return summary, df_flags


if __name__ == "__main__":
    val = ValuationAnalytics()
    val.compute_valuation_summary()
