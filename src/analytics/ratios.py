import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    get_capex_intensity_label,
    get_cfo_quality_badge,
)

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"


def compute_ratios_for_database(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute 50+ financial ratios and KPIs for all company-year pairs and persist to SQLite."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    edge_cases_log: List[str] = []

    with sqlite3.connect(db_path) as conn:
        df_co = pd.read_sql("SELECT id, company_name, face_value, book_value, roce_percentage, roe_percentage FROM companies", conn)
        df_pl = pd.read_sql("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
        df_bs = pd.read_sql("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
        df_cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
        df_sec = pd.read_sql("SELECT company_id, broad_sector, sub_sector FROM sectors", conn)
        df_mc = pd.read_sql("SELECT company_id, year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap", conn)

    # P&L is the primary anchor for annual financial statement periods
    merged = pd.merge(df_pl, df_bs, on=["company_id", "year"], how="left", suffixes=("_pl", "_bs"))
    merged = pd.merge(merged, df_cf, on=["company_id", "year"], how="left", suffixes=("", "_cf"))
    merged = pd.merge(merged, df_sec, on="company_id", how="left")
    merged = pd.merge(merged, df_co[["id", "face_value", "company_name"]].rename(columns={"id": "company_id"}), on="company_id", how="left")

    
    # Sort chronological
    merged = merged.sort_values(by=["company_id", "year"]).reset_index(drop=True)

    # Market cap join key (extract integer year from YYYY-MM)
    merged["cal_year"] = pd.to_numeric(merged["year"].str.slice(0, 4), errors="coerce").fillna(0).astype(int)
    merged = pd.merge(merged, df_mc, left_on=["company_id", "cal_year"], right_on=["company_id", "year"], how="left", suffixes=("", "_mc"))

    rows: List[Dict[str, Any]] = []
    capital_alloc_records: List[Dict[str, Any]] = []
    cashflow_intel_records: List[Dict[str, Any]] = []
    distress_records: List[Dict[str, Any]] = []

    # Process per company to calculate multi-year metrics and CAGRs
    grouped = merged.groupby("company_id")

    for company_id, group in grouped:
        group = group.sort_values("year").reset_index(drop=True)
        n_years = len(group)
        sector = group["broad_sector"].iloc[0] if "broad_sector" in group.columns and pd.notna(group["broad_sector"].iloc[0]) else "Unknown"

        for i, row in group.iterrows():
            yr = row["year"]
            sales = float(row.get("sales") or 0)
            expenses = float(row.get("expenses") or 0)
            op = float(row.get("operating_profit") or 0)
            other_inc = float(row.get("other_income") or 0)
            interest = float(row.get("interest") or 0)
            depr = float(row.get("depreciation") or 0)
            pbt = float(row.get("profit_before_tax") or 0)
            net_profit = float(row.get("net_profit") or 0)
            eps = float(row.get("eps") or 0) if pd.notna(row.get("eps")) else None
            div_payout = float(row.get("dividend_payout") or 0) if pd.notna(row.get("dividend_payout")) else None

            equity_cap = float(row.get("equity_capital") or 0)
            reserves = float(row.get("reserves") or 0)
            total_equity = equity_cap + reserves
            borrowings = float(row.get("borrowings") or 0)
            other_liab = float(row.get("other_liabilities") or 0)
            total_liab = float(row.get("total_liabilities") or 0)
            fixed_assets = float(row.get("fixed_assets") or 0)
            investments = float(row.get("investments") or 0)
            other_assets = float(row.get("other_asset") or 0)
            total_assets = float(row.get("total_assets") or 0)
            face_val = float(row.get("face_value") or 1)

            cfo = float(row.get("operating_activity") or 0) if pd.notna(row.get("operating_activity")) else None
            cfi = float(row.get("investing_activity") or 0) if pd.notna(row.get("investing_activity")) else None
            cff = float(row.get("financing_activity") or 0) if pd.notna(row.get("financing_activity")) else None
            ncf = float(row.get("net_cash_flow") or 0) if pd.notna(row.get("net_cash_flow")) else None

            ebit = op - depr

            # Profitability Ratios
            npm = (net_profit / sales * 100.0) if sales > 0 else None
            opm = (op / sales * 100.0) if sales > 0 else None
            ebit_margin = (ebit / sales * 100.0) if sales > 0 else None

            # Returns
            roe = (net_profit / total_equity * 100.0) if total_equity > 0 else None
            if total_equity <= 0:
                edge_cases_log.append(f"[{company_id} {yr}] Negative or zero equity ({total_equity}): ROE set to None")

            capital_employed = total_equity + borrowings
            roce = (ebit / capital_employed * 100.0) if capital_employed > 0 else None

            roa = (net_profit / total_assets * 100.0) if total_assets > 0 else None

            # Leverage
            de = (borrowings / total_equity) if total_equity > 0 else None
            if borrowings == 0:
                de = 0.0

            if interest == 0:
                icr = None
                edge_cases_log.append(f"[{company_id} {yr}] Interest is 0: ICR displayed as Debt Free (None numeric)")
            else:
                icr = (op + other_inc) / interest

            net_debt = borrowings - investments
            net_debt_ebitda = (net_debt / op) if op > 0 else None

            # Efficiency
            asset_turn = (sales / total_assets) if total_assets > 0 else None
            fa_turn = (sales / fixed_assets) if fixed_assets > 0 else None
            wc_days = ((other_assets - other_liab) / sales * 365.0) if sales > 0 else None

            # Cash flow metrics
            fcf = (cfo + cfi) if (cfo is not None and cfi is not None) else None
            capex = abs(cfi) if cfi is not None else None
            cfo_pat = (cfo / net_profit) if (cfo is not None and net_profit != 0) else None
            capex_intensity = (abs(cfi) / sales * 100.0) if (cfi is not None and sales > 0) else None
            fcf_conversion = (fcf / op * 100.0) if (fcf is not None and op != 0) else None

            # Valuation metrics from market_cap
            mcap = float(row.get("market_cap_crore") or 0) if pd.notna(row.get("market_cap_crore")) else None
            fcf_yield = (fcf / mcap * 100.0) if (fcf is not None and mcap and mcap > 0) else None
            pe_val = float(row.get("pe_ratio") or 0) if pd.notna(row.get("pe_ratio")) else None
            pb_val = float(row.get("pb_ratio") or 0) if pd.notna(row.get("pb_ratio")) else None
            ev_ebitda_val = float(row.get("ev_ebitda") or 0) if pd.notna(row.get("ev_ebitda")) else None
            div_yield_val = float(row.get("dividend_yield_pct") or 0) if pd.notna(row.get("dividend_yield_pct")) else None

            # Per-share metrics
            shares_cnt = (equity_cap / face_val) if face_val > 0 else equity_cap
            bvps = (total_equity / shares_cnt) if shares_cnt > 0 else None

            # Capital allocation classification
            s_cfo, s_cfi, s_cff, cap_label = classify_capital_allocation(cfo, cfi, cff, cfo_pat)
            capital_alloc_records.append({
                "company_id": company_id,
                "year": yr,
                "CFO_sign": s_cfo,
                "CFI_sign": s_cfi,
                "CFF_sign": s_cff,
                "pattern_label": cap_label,
            })

            # Multi-Year CAGRs (3yr, 5yr, 10yr) relative to index i
            # 3-year Revenue & PAT CAGR
            rev_cagr_3 = None
            pat_cagr_3 = None
            cagr_flag_entry = "NORMAL"
            if i >= 3:
                base_sales = float(group.iloc[i - 3].get("sales") or 0)
                base_pat = float(group.iloc[i - 3].get("net_profit") or 0)
                rev_cagr_3, _, _ = calculate_cagr(base_sales, sales, 3)
                pat_cagr_3, flag_pat_3, _ = calculate_cagr(base_pat, net_profit, 3)
                if flag_pat_3 == "TURNAROUND":
                    cagr_flag_entry = "TURNAROUND"
                    edge_cases_log.append(f"[{company_id} {yr}] 3yr PAT CAGR Turnaround detected (base={base_pat}, end={net_profit})")

            # 5-year CAGRs
            rev_cagr_5 = None
            pat_cagr_5 = None
            eps_cagr_5 = None
            fcf_cagr_5 = None
            if i >= 5:
                base_sales = float(group.iloc[i - 5].get("sales") or 0)
                base_pat = float(group.iloc[i - 5].get("net_profit") or 0)
                base_eps = float(group.iloc[i - 5].get("eps") or 0) if pd.notna(group.iloc[i - 5].get("eps")) else None
                base_fcf = (float(group.iloc[i - 5].get("operating_activity") or 0) + float(group.iloc[i - 5].get("investing_activity") or 0)) if pd.notna(group.iloc[i - 5].get("operating_activity")) else None
                
                rev_cagr_5, _, _ = calculate_cagr(base_sales, sales, 5)
                pat_cagr_5, flag_pat_5, _ = calculate_cagr(base_pat, net_profit, 5)
                if base_eps is not None and eps is not None:
                    eps_cagr_5, _, _ = calculate_cagr(base_eps, eps, 5)
                if base_fcf is not None and fcf is not None:
                    fcf_cagr_5, _, _ = calculate_cagr(base_fcf, fcf, 5)

            # 10-year Revenue CAGR
            rev_cagr_10 = None
            if i >= 10:
                base_sales = float(group.iloc[i - 10].get("sales") or 0)
                rev_cagr_10, _, _ = calculate_cagr(base_sales, sales, 10)

            # Check distress pattern: CFO < 0 and CFF > 0
            if (cfo is not None and cfo < 0) and (cff is not None and cff > 0):
                distress_records.append({
                    "company_id": company_id,
                    "year": yr,
                    "cfo": cfo,
                    "cff": cff,
                    "net_profit": net_profit,
                    "reason": "Negative CFO funded by positive financing cash flow (Distress Signal)",
                })

            # Cash flow intelligence snapshot
            if i == n_years - 1:
                # Latest year cash flow intelligence
                # Compute 5-year average CFO / PAT
                recent_cfos = [float(r.get("operating_activity") or 0) for _, r in group.iloc[max(0, i-4):i+1].iterrows() if pd.notna(r.get("operating_activity"))]
                recent_pats = [float(r.get("net_profit") or 0) for _, r in group.iloc[max(0, i-4):i+1].iterrows() if pd.notna(r.get("net_profit"))]
                sum_cfo = sum(recent_cfos)
                sum_pat = sum(recent_pats)
                avg_cfo_pat_5yr = (sum_cfo / sum_pat) if sum_pat != 0 else (cfo_pat or 0)

                cashflow_intel_records.append({
                    "company_id": company_id,
                    "company_name": row.get("company_name", company_id),
                    "sector": sector,
                    "latest_year": yr,
                    "cfo_cr": cfo,
                    "fcf_cr": fcf,
                    "cfo_pat_ratio_5yr": round(avg_cfo_pat_5yr, 2) if avg_cfo_pat_5yr is not None else None,
                    "cfo_quality_score": get_cfo_quality_badge(avg_cfo_pat_5yr),
                    "fcf_cagr_5yr": fcf_cagr_5,
                    "capex_intensity_pct": round(capex_intensity, 2) if capex_intensity is not None else None,
                    "capex_intensity_label": get_capex_intensity_label(capex_intensity),
                    "fcf_conversion_rate_pct": round(fcf_conversion, 2) if fcf_conversion is not None else None,
                    "capital_allocation_label": cap_label,
                })

            row_dict = {
                "company_id": company_id,
                "year": yr,
                "net_profit_margin_pct": round(npm, 2) if npm is not None else None,
                "operating_profit_margin_pct": round(opm, 2) if opm is not None else None,
                "ebit_margin_pct": round(ebit_margin, 2) if ebit_margin is not None else None,
                "return_on_equity_pct": round(roe, 2) if roe is not None else None,
                "roce_pct": round(roce, 2) if roce is not None else None,
                "return_on_assets_pct": round(roa, 2) if roa is not None else None,
                "debt_to_equity": round(de, 2) if de is not None else None,
                "interest_coverage": round(icr, 2) if icr is not None else None,
                "net_debt_cr": round(net_debt, 2) if net_debt is not None else None,
                "net_debt_to_ebitda": round(net_debt_ebitda, 2) if net_debt_ebitda is not None else None,
                "asset_turnover": round(asset_turn, 2) if asset_turn is not None else None,
                "fixed_asset_turnover": round(fa_turn, 2) if fa_turn is not None else None,
                "working_capital_days": round(wc_days, 1) if wc_days is not None else None,
                "revenue_cagr_3yr": rev_cagr_3,
                "revenue_cagr_5yr": rev_cagr_5,
                "revenue_cagr_10yr": rev_cagr_10,
                "pat_cagr_3yr": pat_cagr_3,
                "pat_cagr_5yr": pat_cagr_5,
                "eps_cagr_5yr": eps_cagr_5,
                "free_cash_flow_cr": round(fcf, 2) if fcf is not None else None,
                "capex_cr": round(capex, 2) if capex is not None else None,
                "cfo_pat_ratio": round(cfo_pat, 2) if cfo_pat is not None else None,
                "capex_intensity_pct": round(capex_intensity, 2) if capex_intensity is not None else None,
                "fcf_conversion_rate_pct": round(fcf_conversion, 2) if fcf_conversion is not None else None,
                "fcf_yield_pct": round(fcf_yield, 2) if fcf_yield is not None else None,
                "pe_ratio": round(pe_val, 2) if pe_val is not None else None,
                "pb_ratio": round(pb_val, 2) if pb_val is not None else None,
                "ev_ebitda": round(ev_ebitda_val, 2) if ev_ebitda_val is not None else None,
                "dividend_yield_pct": round(div_yield_val, 2) if div_yield_val is not None else None,
                "dividend_payout_ratio_pct": round(div_payout, 2) if div_payout is not None else None,
                "book_value_per_share": round(bvps, 2) if bvps is not None else None,
                "earnings_per_share": round(eps, 2) if eps is not None else None,
                "capital_allocation_pattern": cap_label,
                "composite_quality_score": None,  # Will compute in batch below
                "cagr_flag": cagr_flag_entry,
            }
            rows.append(row_dict)

    df_ratios = pd.DataFrame(rows)

    # Compute Composite Quality Score per year across universe
    # 0.35 * Profitability + 0.30 * Cash Quality + 0.20 * Growth + 0.15 * Leverage
    for yr, y_group in df_ratios.groupby("year"):
        # Helper to scale column 0-100 using P10/P90 winsorisation
        def score_series(s: pd.Series, ascending: bool = True) -> pd.Series:
            valid = s.dropna()
            if len(valid) < 2:
                return pd.Series(50.0, index=s.index)
            p10 = np.percentile(valid, 10)
            p90 = np.percentile(valid, 90)
            if p90 == p10:
                return pd.Series(50.0, index=s.index)
            clipped = s.clip(lower=p10, upper=p90)
            scaled = (clipped - p10) / (p90 - p10) * 100.0
            if not ascending:
                scaled = 100.0 - scaled
            return scaled.fillna(50.0)

        # Profitability subscores
        s_roe = score_series(y_group["return_on_equity_pct"])
        s_roce = score_series(y_group["roce_pct"])
        s_npm = score_series(y_group["net_profit_margin_pct"])
        prof_score = (s_roe * 0.15 + s_roce * 0.10 + s_npm * 0.10) / 0.35

        # Cash Quality subscores
        s_fcf_cagr = score_series(y_group["free_cash_flow_cr"])
        s_cfo_pat = score_series(y_group["cfo_pat_ratio"])
        s_fcf_pos = y_group["free_cash_flow_cr"].apply(lambda x: 100.0 if (pd.notna(x) and x > 0) else 0.0)
        cash_score = (s_fcf_cagr * 0.15 + s_cfo_pat * 0.10 + s_fcf_pos * 0.05) / 0.30

        # Growth subscores
        s_rev_cagr = score_series(y_group["revenue_cagr_5yr"])
        s_pat_cagr = score_series(y_group["pat_cagr_5yr"])
        growth_score = (s_rev_cagr * 0.10 + s_pat_cagr * 0.10) / 0.20

        # Leverage scores
        # D/E score: 0=100, 0.5=85, 1=70, 2=50, >5=0
        def de_scorer(de_val):
            if pd.isna(de_val): return 50.0
            if de_val <= 0: return 100.0
            if de_val <= 0.5: return 85.0
            if de_val <= 1.0: return 70.0
            if de_val <= 2.0: return 50.0
            if de_val >= 5.0: return 0.0
            return max(0.0, 50.0 - (de_val - 2.0) * (50.0 / 3.0))

        # ICR score: >10=100, 5=75, 3=50, <1.5=0
        def icr_scorer(icr_val):
            if pd.isna(icr_val): return 100.0  # Often debt free
            if icr_val >= 10.0: return 100.0
            if icr_val >= 5.0: return 75.0
            if icr_val >= 3.0: return 50.0
            if icr_val <= 1.5: return 0.0
            return 25.0

        s_de = y_group["debt_to_equity"].apply(de_scorer)
        s_icr = y_group["interest_coverage"].apply(icr_scorer)
        lev_score = (s_de * 0.10 + s_icr * 0.05) / 0.15

        comp_score = (prof_score * 0.35 + cash_score * 0.30 + growth_score * 0.20 + lev_score * 0.15).round(1)
        df_ratios.loc[y_group.index, "composite_quality_score"] = comp_score

    # Save to SQLite table financial_ratios
    with sqlite3.connect(db_path) as conn:
        df_ratios.to_sql("financial_ratios", conn, if_exists="replace", index=False)
        logger.info("Saved %d rows to financial_ratios table in %s", len(df_ratios), db_path)

    # Export Deliverable D-06: capital_allocation.csv
    df_cap = pd.DataFrame(capital_alloc_records)
    df_cap.to_csv(os.path.join(OUTPUT_DIR, "capital_allocation.csv"), index=False)
    logger.info("Saved %d rows to %s/capital_allocation.csv", len(df_cap), OUTPUT_DIR)

    # Export Deliverable D-13: cashflow_intelligence.xlsx
    df_cf_intel = pd.DataFrame(cashflow_intel_records)
    df_cf_intel.to_excel(os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx"), index=False)
    logger.info("Saved %d rows to %s/cashflow_intelligence.xlsx", len(df_cf_intel), OUTPUT_DIR)

    # Export distress alerts CSV
    df_distress = pd.DataFrame(distress_records)
    df_distress.to_csv(os.path.join(OUTPUT_DIR, "distress_alerts.csv"), index=False)

    # Write ratio edge cases log
    with open("ratio_edge_cases.log", "w", encoding="utf-8") as f:
        f.write("\n".join(edge_cases_log))
    logger.info("Saved %d edge case logs to ratio_edge_cases.log", len(edge_cases_log))

    return df_ratios


if __name__ == "__main__":
    compute_ratios_for_database()
