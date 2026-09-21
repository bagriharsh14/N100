import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml
from dotenv import load_dotenv

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
CONFIG_PATH = os.path.join(ROOT_DIR, "config/screener_config.yaml")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output/screener_output.xlsx")


class ScreenerEngine:
    """Multi-parameter stock screener and filter engine."""

    def __init__(self, db_path: str = DB_PATH, config_path: str = CONFIG_PATH) -> None:
        """Initialize screener with database and YAML config."""
        self.db_path = db_path
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load screening thresholds from YAML configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def get_latest_data(self) -> pd.DataFrame:
        """Fetch latest year financial ratios joined with company master and sector tables."""
        query = """
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
            p.net_profit,
            b.borrowings,
            b.total_assets
        FROM latest_years ly
        JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
        JOIN companies c ON r.company_id = c.id
        LEFT JOIN sectors s ON r.company_id = s.company_id
        LEFT JOIN profitandloss p ON r.company_id = p.company_id AND r.year = p.year
        LEFT JOIN balancesheet b ON r.company_id = b.company_id AND r.year = b.year
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn)
        return df

    def run_preset(self, preset_key: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Execute a preset screen on universe data."""
        if df is None:
            df = self.get_latest_data()
        
        filtered = df.copy()
        preset = self.config.get("presets", {}).get(preset_key, {})
        filters = preset.get("filters", {})
        
        # Helper to check if company is financial
        is_financial = filtered["broad_sector"].astype(str).str.lower().str.contains("financial")

        if "min_roe" in filters:
            filtered = filtered[filtered["return_on_equity_pct"] >= filters["min_roe"]]

        if "max_de" in filters:
            # Rule: Skip Financials sector for D/E filter!
            max_de = filters["max_de"]
            is_fin = filtered["broad_sector"].astype(str).str.lower().str.contains("financial")
            if max_de == 0.0:
                filtered = filtered[filtered["debt_to_equity"] == 0]
            else:
                filtered = filtered[is_fin | (filtered["debt_to_equity"] <= max_de)]


        if "min_fcf" in filters:
            filtered = filtered[filtered["free_cash_flow_cr"] > filters["min_fcf"]]

        if "min_revenue_cagr_5yr" in filters:
            filtered = filtered[filtered["revenue_cagr_5yr"] >= filters["min_revenue_cagr_5yr"]]

        if "min_revenue_cagr_3yr" in filters:
            filtered = filtered[filtered["revenue_cagr_3yr"] >= filters["min_revenue_cagr_3yr"]]

        if "min_pat_cagr_5yr" in filters:
            filtered = filtered[filtered["pat_cagr_5yr"] >= filters["min_pat_cagr_5yr"]]

        if "max_pe" in filters:
            filtered = filtered[(filtered["pe_ratio"].notna()) & (filtered["pe_ratio"] > 0) & (filtered["pe_ratio"] <= filters["max_pe"])]

        if "max_pb" in filters:
            filtered = filtered[(filtered["pb_ratio"].notna()) & (filtered["pb_ratio"] <= filters["max_pb"])]

        if "min_dividend_yield" in filters:
            filtered = filtered[filtered["dividend_yield_pct"] >= filters["min_dividend_yield"]]

        if "max_dividend_payout" in filters:
            filtered = filtered[filtered["dividend_payout_ratio_pct"] <= filters["max_dividend_payout"]]

        if "min_sales" in filters:
            filtered = filtered[filtered["sales"] >= filters["min_sales"]]

        ranking_metric = preset.get("ranking_metric", "composite_quality_score")
        sort_asc = preset.get("sort_ascending", False)
        
        if ranking_metric in filtered.columns:
            filtered = filtered.sort_values(by=ranking_metric, ascending=sort_asc)

        return filtered

    def run_custom_filter(
        self,
        min_roe: Optional[float] = None,
        max_de: Optional[float] = None,
        min_fcf: Optional[float] = None,
        sector: Optional[str] = None,
        min_rev_cagr_5yr: Optional[float] = None,
        min_pat_cagr_5yr: Optional[float] = None,
        max_pe: Optional[float] = None,
        df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Run ad-hoc filtering query for dashboard and REST API."""
        if df is None:
            df = self.get_latest_data()
        
        res = df.copy()
        if sector and sector.lower() != "all":
            res = res[res["broad_sector"].str.lower() == sector.lower()]

        if min_roe is not None:
            res = res[res["return_on_equity_pct"] >= min_roe]

        if max_de is not None:
            is_financial = res["broad_sector"].astype(str).str.lower().str.contains("financial")
            res = res[is_financial | (res["debt_to_equity"] <= max_de)]

        if min_fcf is not None:
            res = res[res["free_cash_flow_cr"] >= min_fcf]

        if min_rev_cagr_5yr is not None:
            res = res[res["revenue_cagr_5yr"] >= min_rev_cagr_5yr]

        if min_pat_cagr_5yr is not None:
            res = res[res["pat_cagr_5yr"] >= min_pat_cagr_5yr]

        if max_pe is not None:
            res = res[(res["pe_ratio"].notna()) & (res["pe_ratio"] > 0) & (res["pe_ratio"] <= max_pe)]

        return res.sort_values(by="composite_quality_score", ascending=False)

    def export_all_presets_excel(self, output_path: str = OUTPUT_PATH) -> None:
        """Export all 6 preset screens into an Excel workbook with formatted sheets."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_latest = self.get_latest_data()
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for key, meta in self.config.get("presets", {}).items():
                res = self.run_preset(key, df_latest)
                cols_to_show = [
                    "ticker", "company_name", "broad_sector", "sub_sector",
                    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "operating_profit_margin_pct",
                    "debt_to_equity", "interest_coverage", "free_cash_flow_cr",
                    "revenue_cagr_5yr", "pat_cagr_5yr", "revenue_cagr_3yr",
                    "pe_ratio", "pb_ratio", "dividend_yield_pct", "fcf_yield_pct",
                    "capital_allocation_pattern", "composite_quality_score"
                ]
                available_cols = [c for c in cols_to_show if c in res.columns]
                sheet_name = meta.get("name", key)[:31]
                res[available_cols].to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info("Exported all screener preset results to %s", output_path)


if __name__ == "__main__":
    engine = ScreenerEngine()
    engine.export_all_presets_excel()
