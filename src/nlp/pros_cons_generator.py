import logging
import os
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


class ProsConsGenerator:
    """Rule-based qualitative insights generator for Nifty 100 companies."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize generator."""
        self.db_path = db_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def generate_all_pros_cons(self) -> pd.DataFrame:
        """Generate structured pros and cons for all 92 companies."""
        with sqlite3.connect(self.db_path) as conn:
            df_co = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
            df_sec = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
            
            query = """
            WITH latest_years AS (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            )
            SELECT r.* FROM latest_years ly
            JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
            """
            df_r = pd.read_sql(query, conn)

        merged = pd.merge(df_co, df_sec, on="company_id", how="left")
        merged = pd.merge(merged, df_r, on="company_id", how="left")

        insights: List[Dict[str, Any]] = []

        for _, row in merged.iterrows():
            cid = row["company_id"]
            sec = str(row.get("broad_sector", "")).lower()
            is_financial = "financial" in sec

            roe = row.get("return_on_equity_pct")
            roce = row.get("roce_pct")
            npm = row.get("net_profit_margin_pct")
            opm = row.get("operating_profit_margin_pct")
            de = row.get("debt_to_equity")
            icr = row.get("interest_coverage")
            fcf = row.get("free_cash_flow_cr")
            cfo_pat = row.get("cfo_pat_ratio")
            rev_cagr_5 = row.get("revenue_cagr_5yr")
            pat_cagr_5 = row.get("pat_cagr_5yr")
            div_yield = row.get("dividend_yield_pct")
            div_payout = row.get("dividend_payout_ratio_pct")
            pe = row.get("pe_ratio")
            wc_days = row.get("working_capital_days")
            capex_int = row.get("capex_intensity_pct")
            score = row.get("composite_quality_score")

            pros_count = 0
            cons_count = 0

            # ---------------- PRO RULES ----------------
            if pd.notna(roe) and roe >= 20.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "ROE_GT_20", "text": f"Company has delivered superior Return on Equity of {roe:.1f}%", "confidence_pct": 95})
                pros_count += 1

            if pd.notna(roce) and roce >= 20.0 and not is_financial:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "ROCE_GT_20", "text": f"Strong capital efficiency with ROCE at {roce:.1f}%", "confidence_pct": 90})
                pros_count += 1

            if pd.notna(de) and de == 0.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "DEBT_FREE", "text": "Company is virtually debt-free with zero borrowings", "confidence_pct": 98})
                pros_count += 1

            if pd.notna(fcf) and fcf > 0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "POSITIVE_FCF", "text": f"Generates positive Free Cash Flow of ₹{fcf:,.0f} Cr", "confidence_pct": 92})
                pros_count += 1

            if pd.notna(rev_cagr_5) and rev_cagr_5 >= 12.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "REV_CAGR_GT_12", "text": f"Steady revenue growth compounding at {rev_cagr_5:.1f}% CAGR over 5 years", "confidence_pct": 88})
                pros_count += 1

            if pd.notna(pat_cagr_5) and pat_cagr_5 >= 15.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "PAT_CAGR_GT_15", "text": f"Robust profit growth compounding at {pat_cagr_5:.1f}% CAGR over 5 years", "confidence_pct": 88})
                pros_count += 1

            if pd.notna(cfo_pat) and cfo_pat >= 1.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "HIGH_CFO_PAT", "text": "High cash conversion quality with CFO exceeding reported net profit", "confidence_pct": 85})
                pros_count += 1

            if pd.notna(div_yield) and div_yield >= 2.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "ATTRACTIVE_DIV_YIELD", "text": f"Offers an attractive dividend yield of {div_yield:.1f}% (SIMULATED)", "confidence_pct": 82})
                pros_count += 1

            if pd.notna(opm) and opm >= 20.0 and not is_financial:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "HEALTHY_OPM", "text": f"Healthy operating margin of {opm:.1f}%", "confidence_pct": 85})
                pros_count += 1

            if pd.notna(score) and score >= 65.0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "TOP_COMPOSITE_SCORE", "text": f"Ranks favorably on overall composite financial health index ({score:.1f}/100)", "confidence_pct": 80})
                pros_count += 1

            # Fallback Pro to ensure >= 1 pro for all 92 companies
            if pros_count == 0:
                insights.append({"company_id": cid, "type": "pro", "rule_triggered": "ESTABLISHED_LARGE_CAP", "text": "Established constituent of Nifty 100 with significant market presence", "confidence_pct": 75})

            # ---------------- CON RULES ----------------
            if pd.notna(de) and de >= 2.0 and not is_financial:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "HIGH_LEVERAGE", "text": f"Elevated leverage with Debt-to-Equity ratio of {de:.2f}x", "confidence_pct": 92})
                cons_count += 1

            if pd.notna(fcf) and fcf < 0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "NEGATIVE_FCF", "text": f"Free cash flow is negative at ₹{fcf:,.0f} Cr due to heavy reinvestment/working capital", "confidence_pct": 90})
                cons_count += 1

            if pd.notna(roe) and roe < 10.0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "LOW_ROE", "text": f"Subdued Return on Equity at {roe:.1f}%, below large-cap historical averages", "confidence_pct": 88})
                cons_count += 1

            if pd.notna(icr) and icr < 2.5 and icr > 0 and not is_financial:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "LOW_ICR", "text": f"Low interest coverage of {icr:.1f}x reflects interest burden on operating profit", "confidence_pct": 85})
                cons_count += 1

            if pd.notna(rev_cagr_5) and rev_cagr_5 < 5.0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "SLOW_REV_GROWTH", "text": f"Modest 5-year revenue CAGR of {rev_cagr_5:.1f}%", "confidence_pct": 82})
                cons_count += 1

            if pd.notna(pat_cagr_5) and pat_cagr_5 < 0.0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "NEGATIVE_PAT_GROWTH", "text": "Net profit has contracted over the 5-year historical horizon", "confidence_pct": 85})
                cons_count += 1

            if pd.notna(cfo_pat) and cfo_pat < 0.5:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "LOW_CFO_PAT", "text": f"Low cash conversion (CFO/PAT = {cfo_pat:.2f}), suggesting accrual buildup", "confidence_pct": 80})
                cons_count += 1

            if pd.notna(pe) and pe >= 45.0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "PREMIUM_VALUATION", "text": f"Trades at an elevated valuation multiple of {pe:.1f}x P/E (SIMULATED)", "confidence_pct": 80})
                cons_count += 1

            if pd.notna(wc_days) and wc_days > 120 and not is_financial:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "HIGH_WC_DAYS", "text": f"Working capital cycle is extended at {wc_days:.0f} days", "confidence_pct": 78})
                cons_count += 1

            if pd.notna(capex_int) and capex_int > 15.0 and not is_financial:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "HIGH_CAPEX_INTENSITY", "text": f"High CapEx intensity ({capex_int:.1f}% of sales) requires continuous capital deployment", "confidence_pct": 75})
                cons_count += 1

            # Fallback Con to ensure >= 1 con for all 92 companies
            if cons_count == 0:
                insights.append({"company_id": cid, "type": "con", "rule_triggered": "GENERAL_MARKET_CYCLICALITY", "text": "Performance subject to sector cyclicality and broader macroeconomic fluctuations", "confidence_pct": 70})

        df_out = pd.DataFrame(insights)
        out_path = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")
        df_out.to_csv(out_path, index=False)
        logger.info("Saved %d generated pros/cons across %d companies to %s", len(df_out), df_out["company_id"].nunique(), out_path)
        return df_out


if __name__ == "__main__":
    gen = ProsConsGenerator()
    gen.generate_all_pros_cons()
