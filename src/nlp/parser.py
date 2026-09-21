import logging
import os
import re
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"


def parse_growth_string(text: Any) -> List[Dict[str, Any]]:
    """Extract (period_years, value_pct) pairs from freeform multi-period CAGR text."""
    if text is None or pd.isna(text):
        return []
    
    results = []
    # Matches patterns like '10 Years: 21%', '5 Years: 6%', '3 Years: 15%', 'TTM: 12%'
    pattern = r"(\d+)\s*Years?:?\s*([+-]?[\d.]+)%"
    matches = re.findall(pattern, str(text), re.IGNORECASE)
    for m in matches:
        try:
            yrs = int(m[0])
            val = float(m[1])
            results.append({"period_years": yrs, "value_pct": val})
        except (ValueError, TypeError):
            continue
            
    # TTM pattern
    m_ttm = re.search(r"TTM:?\s*([+-]?[\d.]+)%", str(text), re.IGNORECASE)
    if m_ttm:
        try:
            results.append({"period_years": 1, "value_pct": float(m_ttm.group(1))})
        except (ValueError, TypeError):
            pass
            
    return results


def parse_all_analysis_records(db_path: str = DB_PATH) -> pd.DataFrame:
    """Parse analysis table into structured numeric DataFrame and cross-validate."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df_an = pd.read_sql("SELECT * FROM analysis", conn)
        df_ratios = pd.read_sql("SELECT company_id, MAX(year) AS latest_year, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios GROUP BY company_id", conn)

    parsed_rows: List[Dict[str, Any]] = []

    for _, row in df_an.iterrows():
        cid = str(row["company_id"]).strip().upper()
        
        # Sales Growth
        for p in parse_growth_string(row.get("compounded_sales_growth")):
            parsed_rows.append({
                "company_id": cid,
                "metric_type": "compounded_sales_growth",
                "period_years": p["period_years"],
                "value_pct": p["value_pct"],
            })

        # Profit Growth
        for p in parse_growth_string(row.get("compounded_profit_growth")):
            parsed_rows.append({
                "company_id": cid,
                "metric_type": "compounded_profit_growth",
                "period_years": p["period_years"],
                "value_pct": p["value_pct"],
            })

        # Stock Price CAGR
        for p in parse_growth_string(row.get("stock_price_cagr")):
            parsed_rows.append({
                "company_id": cid,
                "metric_type": "stock_price_cagr",
                "period_years": p["period_years"],
                "value_pct": p["value_pct"],
            })

        # ROE
        for p in parse_growth_string(row.get("roe")):
            parsed_rows.append({
                "company_id": cid,
                "metric_type": "roe",
                "period_years": p["period_years"],
                "value_pct": p["value_pct"],
            })

    df_parsed = pd.DataFrame(parsed_rows)
    # Deliverable D-15: analysis_parsed.csv
    out_path = os.path.join(OUTPUT_DIR, "analysis_parsed.csv")
    df_parsed.to_csv(out_path, index=False)
    logger.info("Saved %d parsed analysis rows to %s", len(df_parsed), out_path)

    # Cross-validate 5-year sales growth
    cross_val_rows = []
    for _, row in df_parsed[df_parsed["period_years"] == 5].iterrows():
        cid = row["company_id"]
        mtype = row["metric_type"]
        val_parsed = row["value_pct"]
        r_match = df_ratios[df_ratios["company_id"] == cid]
        if not r_match.empty:
            computed_val = None
            if mtype == "compounded_sales_growth":
                computed_val = r_match["revenue_cagr_5yr"].iloc[0]
            elif mtype == "compounded_profit_growth":
                computed_val = r_match["pat_cagr_5yr"].iloc[0]
            
            diff = abs(val_parsed - computed_val) if computed_val is not None and pd.notna(computed_val) else None
            cross_val_rows.append({
                "company_id": cid,
                "metric": mtype,
                "parsed_value_5yr": val_parsed,
                "computed_value_5yr": computed_val,
                "difference": round(diff, 2) if diff is not None else None,
                "divergence_gt_5pct": (diff > 5.0) if diff is not None else False
            })

    df_cv = pd.DataFrame(cross_val_rows)
    df_cv.to_csv(os.path.join(OUTPUT_DIR, "cross_validation.csv"), index=False)
    logger.info("Saved cross-validation results to %s/cross_validation.csv", OUTPUT_DIR)

    return df_parsed


if __name__ == "__main__":
    parse_all_analysis_records()
