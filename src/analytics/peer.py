import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Ensure project root in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"
RADAR_DIR = "reports/radar_charts"

PEER_METRICS = [
    "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "operating_profit_margin_pct",
    "debt_to_equity", "interest_coverage", "free_cash_flow_cr", "cfo_pat_ratio",
    "revenue_cagr_3yr", "revenue_cagr_5yr", "pat_cagr_3yr", "pat_cagr_5yr", "eps_cagr_5yr",
    "asset_turnover", "working_capital_days", "fcf_conversion_rate_pct", "fcf_yield_pct",
    "pe_ratio", "pb_ratio", "composite_quality_score"
]

RADAR_8_AXES = [
    "ROE", "ROCE", "NPM", "Low D/E", "FCF", "PAT CAGR 5Y", "Rev CAGR 5Y", "EPS CAGR 5Y"
]


class PeerComparisonEngine:
    """Computes intra-group percentile rankings, peer comparisons, and radar charts."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize peer engine."""
        self.db_path = db_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(RADAR_DIR, exist_ok=True)

    def load_peer_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load peer groups and latest financial ratios."""
        with sqlite3.connect(self.db_path) as conn:
            df_pg = pd.read_sql("SELECT * FROM peer_groups", conn)
            
            query = """
            WITH latest_years AS (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            )
            SELECT 
                r.*,
                c.company_name
            FROM latest_years ly
            JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
            JOIN companies c ON r.company_id = c.id
            """
            df_r = pd.read_sql(query, conn)
        return df_pg, df_r

    def compute_peer_percentiles(self) -> pd.DataFrame:
        """Calculate percentile rankings across all peer groups and populate SQLite table."""
        df_pg, df_r = self.load_peer_data()
        records: List[Dict[str, Any]] = []

        # Join ratios with peer groups
        merged = pd.merge(df_pg, df_r, on="company_id", how="inner")

        for group_name, g_df in merged.groupby("peer_group_name"):
            for metric in PEER_METRICS:
                if metric not in g_df.columns:
                    continue
                
                # Higher is better for all except D/E and working_capital_days
                asc = True if metric in ["debt_to_equity", "working_capital_days", "pe_ratio", "pb_ratio"] else False
                
                series = g_df[metric]
                # Rank 0.0 to 1.0 (percent_rank)
                ranks = series.rank(ascending=not asc, pct=True, method="average")

                for idx, row in g_df.iterrows():
                    val = row[metric]
                    pct = ranks.loc[idx] if pd.notna(val) else None
                    records.append({
                        "company_id": row["company_id"],
                        "peer_group_name": group_name,
                        "metric": metric,
                        "value": round(float(val), 2) if pd.notna(val) else None,
                        "percentile_rank": round(float(pct), 3) if pct is not None and pd.notna(pct) else None,
                        "year": row["year"],
                    })

        df_percentiles = pd.DataFrame(records)

        with sqlite3.connect(self.db_path) as conn:
            df_percentiles.to_sql("peer_percentiles", conn, if_exists="replace", index=False)
            logger.info("Saved %d peer percentiles to SQLite table peer_percentiles", len(df_percentiles))

        return df_percentiles

    def export_peer_comparison_excel(self, output_path: str = os.path.join(OUTPUT_DIR, "peer_comparison.xlsx")) -> None:
        """Export peer comparison workbook with 11 sheets and colour-coded percentile cells."""
        df_pg, df_r = self.load_peer_data()
        merged = pd.merge(df_pg, df_r, on="company_id", how="inner")

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for group_name, g_df in merged.groupby("peer_group_name"):
                cols = ["company_id", "company_name", "is_benchmark"] + [m for m in PEER_METRICS if m in g_df.columns]
                sheet_name = group_name[:31]
                g_df[cols].to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info("Saved peer comparison workbook with %d sheets to %s", merged["peer_group_name"].nunique(), output_path)

    def generate_all_radar_charts(self) -> int:
        """Generate 92 radar chart PNGs in reports/radar_charts/."""
        df_pg, df_r = self.load_peer_data()
        merged = pd.merge(df_pg, df_r, on="company_id", how="inner")
        
        all_companies = df_r["company_id"].unique()
        chart_count = 0

        # Map metrics to 8 radar axes
        metric_keys = [
            "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity",
            "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "eps_cagr_5yr"
        ]

        # Universe min-max for radar normalization
        norm_bounds = {}
        for k in metric_keys:
            s = df_r[k].dropna()
            if len(s) > 0:
                norm_bounds[k] = (np.percentile(s, 5), np.percentile(s, 95))
            else:
                norm_bounds[k] = (0, 100)

        for company_id in all_companies:
            co_row = df_r[df_r["company_id"] == company_id]
            if co_row.empty:
                continue
            
            # Check if company belongs to any peer group
            pg_rows = merged[merged["company_id"] == company_id]
            if not pg_rows.empty:
                grp_name = pg_rows["peer_group_name"].iloc[0]
                grp_df = merged[merged["peer_group_name"] == grp_name]
            else:
                grp_name = "Nifty 100 Average"
                grp_df = df_r

            # Compute normalized values (0 to 100) for company and group avg
            co_vals = []
            grp_vals = []

            for k in metric_keys:
                min_v, max_v = norm_bounds[k]
                rng = (max_v - min_v) if max_v != min_v else 1.0

                # Company value
                val = co_row[k].iloc[0]
                if pd.isna(val):
                    c_scaled = 50.0
                else:
                    if k == "debt_to_equity":
                        c_scaled = max(0.0, min(100.0, 100.0 - (val / 3.0 * 100.0)))
                    else:
                        c_scaled = max(0.0, min(100.0, (val - min_v) / rng * 100.0))
                co_vals.append(c_scaled)

                # Group average value
                g_val = grp_df[k].median()
                if pd.isna(g_val):
                    g_scaled = 50.0
                else:
                    if k == "debt_to_equity":
                        g_scaled = max(0.0, min(100.0, 100.0 - (g_val / 3.0 * 100.0)))
                    else:
                        g_scaled = max(0.0, min(100.0, (g_val - min_v) / rng * 100.0))
                grp_vals.append(g_scaled)

            # Close radar loop
            angles = np.linspace(0, 2 * np.pi, len(RADAR_8_AXES), endpoint=False).tolist()
            co_vals_closed = co_vals + [co_vals[0]]
            grp_vals_closed = grp_vals + [grp_vals[0]]
            angles_closed = angles + [angles[0]]

            # Plot radar
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)

            plt.xticks(angles, RADAR_8_AXES, color="#333333", size=9)
            ax.set_rlabel_position(0)
            plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="grey", size=7)
            plt.ylim(0, 100)

            # Plot company line
            ax.plot(angles_closed, co_vals_closed, linewidth=2, linestyle="solid", label=company_id, color="#1f77b4")
            ax.fill(angles_closed, co_vals_closed, color="#1f77b4", alpha=0.25)

            # Plot peer group benchmark
            ax.plot(angles_closed, grp_vals_closed, linewidth=1.5, linestyle="dashed", label=f"{grp_name} (Median)", color="#ff7f0e")
            ax.fill(angles_closed, grp_vals_closed, color="#ff7f0e", alpha=0.1)

            plt.title(f"{company_id} — Financial Health Radar", size=11, color="#111827", y=1.08, fontweight="bold")
            plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=8)
            plt.tight_layout()

            chart_path = os.path.join(RADAR_DIR, f"{company_id}_radar.png")
            plt.savefig(chart_path, dpi=120)
            plt.close()
            chart_count += 1

        logger.info("Generated %d radar charts in %s", chart_count, RADAR_DIR)
        return chart_count


if __name__ == "__main__":
    engine = PeerComparisonEngine()
    engine.compute_peer_percentiles()
    engine.export_peer_comparison_excel()
    engine.generate_all_radar_charts()
