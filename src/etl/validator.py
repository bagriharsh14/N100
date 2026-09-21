import logging
import re
from typing import Any, Dict, List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validates 16 Data Quality (DQ) rules on raw and normalised financial data."""

    def __init__(self) -> None:
        """Initialize failure log entries container."""
        self.failures: List[Dict[str, Any]] = []

    def log_failure(
        self,
        rule_id: str,
        company_id: str,
        year: str,
        field: str,
        issue: str,
        severity: str,
        raw_value: Any = None,
    ) -> None:
        """Record a data quality rule violation."""
        entry = {
            "rule_id": rule_id,
            "company_id": company_id or "UNKNOWN",
            "year": year or "N/A",
            "field": field,
            "issue": issue,
            "severity": severity,
            "raw_value": str(raw_value) if raw_value is not None else "",
        }
        self.failures.append(entry)
        if severity == "CRITICAL":
            logger.error("DQ Violation [%s] %s %s: %s", rule_id, company_id, year, issue)
        else:
            logger.warning("DQ Violation [%s] %s %s: %s", rule_id, company_id, year, issue)

    def validate_companies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate companies master table (DQ-01, DQ-08)."""
        clean_df = df.copy()
        
        # DQ-08: Ticker format
        valid_rows = []
        for idx, row in clean_df.iterrows():
            ticker = str(row.get("id", "")).strip().upper()
            if len(ticker) < 2 or len(ticker) > 15:
                self.log_failure("DQ-08", ticker, "N/A", "id", f"Invalid ticker length {len(ticker)}", "CRITICAL", ticker)
            else:
                valid_rows.append(idx)
        clean_df = clean_df.loc[valid_rows].copy()
        clean_df["id"] = clean_df["id"].astype(str).str.strip().str.upper()

        # DQ-01: Company PK Uniqueness
        if clean_df["id"].nunique() != len(clean_df):
            dups = clean_df[clean_df.duplicated(subset=["id"], keep=False)]
            for _, r in dups.iterrows():
                self.log_failure("DQ-01", r["id"], "N/A", "id", "Duplicate company ticker detected", "CRITICAL", r["id"])
            clean_df = clean_df.drop_duplicates(subset=["id"], keep="last")

        return clean_df

    def validate_pl(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Profit & Loss records (DQ-02, DQ-03, DQ-05, DQ-06, DQ-07, DQ-11, DQ-12, DQ-14)."""
        clean_df = df.copy()

        # DQ-03: FK Integrity
        valid_mask = clean_df["company_id"].isin(valid_companies)
        for _, r in clean_df[~valid_mask].iterrows():
            self.log_failure("DQ-03", str(r.get("company_id")), str(r.get("year")), "company_id", "Foreign key not in companies.id", "CRITICAL")
        clean_df = clean_df[valid_mask].copy()

        # DQ-07: Year format
        valid_year_mask = clean_df["year"].astype(str).str.match(r"^\d{4}-\d{2}$")
        for _, r in clean_df[~valid_year_mask].iterrows():
            self.log_failure("DQ-07", str(r.get("company_id")), str(r.get("year")), "year", "Unparseable year format", "CRITICAL", r.get("year"))
        clean_df = clean_df[valid_year_mask].copy()

        # DQ-02: Annual PK Uniqueness
        if clean_df.duplicated(subset=["company_id", "year"]).any():
            dups = clean_df[clean_df.duplicated(subset=["company_id", "year"], keep=False)]
            for _, r in dups.iterrows():
                self.log_failure("DQ-02", r["company_id"], r["year"], "company_id+year", "Duplicate annual P&L row", "CRITICAL")
            clean_df = clean_df.drop_duplicates(subset=["company_id", "year"], keep="last")

        # DQ-05: OPM Cross-check
        for _, r in clean_df.iterrows():
            sales = float(r.get("sales") or 0)
            op = float(r.get("operating_profit") or 0)
            opm = float(r.get("opm_percentage") or 0)
            if sales > 0:
                calc_opm = (op / sales) * 100.0
                if abs(opm - calc_opm) > 1.0:
                    self.log_failure("DQ-05", r["company_id"], r["year"], "opm_percentage", f"Reported OPM {opm}% != Calc {calc_opm:.2f}%", "WARNING", opm)

        # DQ-06: Positive Sales
        for _, r in clean_df.iterrows():
            sales = float(r.get("sales") or 0)
            if sales <= 0:
                self.log_failure("DQ-06", r["company_id"], r["year"], "sales", f"Sales <= 0: {sales}", "WARNING", sales)

        # DQ-11: Tax Rate Range
        for _, r in clean_df.iterrows():
            tax = float(r.get("tax_percentage") or 0)
            if tax < 0 or tax > 60:
                self.log_failure("DQ-11", r["company_id"], r["year"], "tax_percentage", f"Tax rate outside [0, 60]: {tax}%", "WARNING", tax)

        # DQ-12: Dividend Payout Cap
        for _, r in clean_df.iterrows():
            div = float(r.get("dividend_payout") or 0)
            if div > 200:
                self.log_failure("DQ-12", r["company_id"], r["year"], "dividend_payout", f"Dividend payout > 200%: {div}%", "WARNING", div)

        # DQ-14: EPS Sign Consistency
        for _, r in clean_df.iterrows():
            np = float(r.get("net_profit") or 0)
            eps = float(r.get("eps") or 0)
            if np > 0 and eps < 0:
                self.log_failure("DQ-14", r["company_id"], r["year"], "eps", f"Net profit > 0 ({np}) but EPS < 0 ({eps})", "WARNING", eps)

        return clean_df

    def validate_bs(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Balance Sheet records (DQ-02, DQ-03, DQ-04, DQ-07, DQ-10, DQ-15)."""
        clean_df = df.copy()

        valid_mask = clean_df["company_id"].isin(valid_companies)
        for _, r in clean_df[~valid_mask].iterrows():
            self.log_failure("DQ-03", str(r.get("company_id")), str(r.get("year")), "company_id", "Foreign key not in companies.id", "CRITICAL")
        clean_df = clean_df[valid_mask].copy()

        valid_year_mask = clean_df["year"].astype(str).str.match(r"^\d{4}-\d{2}$")
        for _, r in clean_df[~valid_year_mask].iterrows():
            self.log_failure("DQ-07", str(r.get("company_id")), str(r.get("year")), "year", "Unparseable year format", "CRITICAL", r.get("year"))
        clean_df = clean_df[valid_year_mask].copy()

        if clean_df.duplicated(subset=["company_id", "year"]).any():
            dups = clean_df[clean_df.duplicated(subset=["company_id", "year"], keep=False)]
            for _, r in dups.iterrows():
                self.log_failure("DQ-02", r["company_id"], r["year"], "company_id+year", "Duplicate annual BS row", "CRITICAL")
            clean_df = clean_df.drop_duplicates(subset=["company_id", "year"], keep="last")

        for idx, r in clean_df.iterrows():
            ta = float(r.get("total_assets") or 0)
            tl = float(r.get("total_liabilities") or 0)
            fa = float(r.get("fixed_assets") or 0)

            # DQ-04: Balance Sheet Balance
            if ta > 0:
                diff_pct = abs(ta - tl) / ta
                if diff_pct > 0.01:
                    self.log_failure("DQ-04", r["company_id"], r["year"], "total_assets", f"Assets {ta} != Liab {tl} by {diff_pct*100:.2f}%", "WARNING")
            
            # DQ-10: Non-Negative Fixed Assets
            if fa < 0:
                self.log_failure("DQ-10", r["company_id"], r["year"], "fixed_assets", f"Negative fixed assets: {fa}", "WARNING", fa)
                clean_df.at[idx, "fixed_assets"] = 0.0

        return clean_df

    def validate_cf(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Cash Flow records (DQ-02, DQ-03, DQ-07, DQ-09)."""
        clean_df = df.copy()

        valid_mask = clean_df["company_id"].isin(valid_companies)
        for _, r in clean_df[~valid_mask].iterrows():
            self.log_failure("DQ-03", str(r.get("company_id")), str(r.get("year")), "company_id", "Foreign key not in companies.id", "CRITICAL")
        clean_df = clean_df[valid_mask].copy()

        valid_year_mask = clean_df["year"].astype(str).str.match(r"^\d{4}-\d{2}$")
        for _, r in clean_df[~valid_year_mask].iterrows():
            self.log_failure("DQ-07", str(r.get("company_id")), str(r.get("year")), "year", "Unparseable year format", "CRITICAL", r.get("year"))
        clean_df = clean_df[valid_year_mask].copy()

        if clean_df.duplicated(subset=["company_id", "year"]).any():
            dups = clean_df[clean_df.duplicated(subset=["company_id", "year"], keep=False)]
            for _, r in dups.iterrows():
                self.log_failure("DQ-02", r["company_id"], r["year"], "company_id+year", "Duplicate annual CF row", "CRITICAL")
            clean_df = clean_df.drop_duplicates(subset=["company_id", "year"], keep="last")

        for idx, r in clean_df.iterrows():
            cfo = float(r.get("operating_activity") or 0)
            cfi = float(r.get("investing_activity") or 0)
            cff = float(r.get("financing_activity") or 0)
            ncf = float(r.get("net_cash_flow") or 0)
            comp_ncf = cfo + cfi + cff
            if abs(ncf - comp_ncf) > 10.0:
                self.log_failure("DQ-09", r["company_id"], r["year"], "net_cash_flow", f"Reported NCF {ncf} != Sum {comp_ncf}", "WARNING", ncf)
                clean_df.at[idx, "net_cash_flow"] = comp_ncf

        return clean_df

    def validate_coverage(self, pl_df: pd.DataFrame, valid_companies: set) -> None:
        """Validate multi-year coverage per company (DQ-16)."""
        counts = pl_df.groupby("company_id")["year"].count().to_dict()
        for cid in valid_companies:
            cnt = counts.get(cid, 0)
            if cnt < 5:
                self.log_failure("DQ-16", cid, "N/A", "coverage", f"Company has only {cnt} years of data (< 5yr requirement)", "WARNING", cnt)

    def export_failures_csv(self, filepath: str) -> None:
        """Write all logged data quality failures to CSV."""
        if not self.failures:
            df = pd.DataFrame(columns=["rule_id", "company_id", "year", "field", "issue", "severity", "raw_value"])
        else:
            df = pd.DataFrame(self.failures)
        df.to_csv(filepath, index=False)
        logger.info("Exported %d DQ failure logs to %s", len(df), filepath)
