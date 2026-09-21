import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from dotenv import load_dotenv
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"

CLUSTER_NAMES = [
    "High-Quality Growth",
    "Defensive Cash Generator",
    "Value Cyclicals",
    "Capital Intensive / Turnaround",
    "Moderate Growth Compounders",
]


class StatisticalClusteringEngine:
    """Performs statistical clustering, outlier analysis, and correlation heatmaps on Nifty 100."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """Initialize engine."""
        self.db_path = db_path
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def load_latest_universe(self) -> pd.DataFrame:
        """Load latest ratios joined with company and sector metadata."""
        query = """
        WITH latest_years AS (
            SELECT company_id, MAX(year) AS max_year
            FROM financial_ratios
            GROUP BY company_id
        )
        SELECT 
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            r.*
        FROM latest_years ly
        JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
        JOIN companies c ON r.company_id = c.id
        LEFT JOIN sectors s ON r.company_id = s.company_id
        """
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn)
        return df

    def perform_kmeans_clustering(self, n_clusters: int = 5) -> pd.DataFrame:
        """Execute KMeans clustering on 5 core features and export cluster_labels.csv."""
        df = self.load_latest_universe()
        feature_cols = [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "free_cash_flow_cr",
            "operating_profit_margin_pct",
        ]

        # Impute missing values with sector median or column median
        X_df = df[feature_cols].copy()
        for col in feature_cols:
            median_val = X_df[col].median()
            X_df[col] = X_df[col].fillna(median_val)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_df)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = kmeans.fit_predict(X_scaled)
        
        # Calculate distance to respective cluster centroid
        centroids = kmeans.cluster_centers_
        distances = []
        for idx, cid in enumerate(cluster_ids):
            dist = np.linalg.norm(X_scaled[idx] - centroids[cid])
            distances.append(round(float(dist), 3))

        df["cluster_id"] = cluster_ids
        df["cluster_name"] = [CLUSTER_NAMES[cid % len(CLUSTER_NAMES)] for cid in cluster_ids]
        df["distance_from_centroid"] = distances

        # Deliverable D-19: cluster_labels.csv
        out_cols = ["company_id", "company_name", "broad_sector", "cluster_id", "cluster_name", "distance_from_centroid"]
        df_labels = df[out_cols].copy()
        out_path = os.path.join(OUTPUT_DIR, "cluster_labels.csv")
        df_labels.to_csv(out_path, index=False)
        logger.info("Saved %d cluster labels to %s", len(df_labels), out_path)

        return df

    def generate_correlation_matrix(self) -> None:
        """Compute Pearson correlation matrix of 10 KPIs and export heatmap PNG."""
        df = self.load_latest_universe()
        core_10_kpis = [
            "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "operating_profit_margin_pct",
            "debt_to_equity", "interest_coverage", "free_cash_flow_cr", "revenue_cagr_5yr",
            "pat_cagr_5yr", "composite_quality_score"
        ]
        kpi_df = df[[c for c in core_10_kpis if c in df.columns]].dropna()

        corr = kpi_df.corr(method="pearson")

        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, cbar=True)
        plt.title("Nifty 100 Financial KPI Pearson Correlation Heatmap", fontsize=12, fontweight="bold", pad=12)
        plt.tight_layout()

        heatmap_path = os.path.join(OUTPUT_DIR, "correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=150)
        plt.close()
        logger.info("Saved correlation heatmap to %s", heatmap_path)

    def generate_portfolio_statistics(self) -> pd.DataFrame:
        """Compute P10, P25, P50, P75, P90, Mean, and Std for 10 core KPIs across all 92 companies."""
        df = self.load_latest_universe()
        core_10_kpis = [
            "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "operating_profit_margin_pct",
            "debt_to_equity", "interest_coverage", "free_cash_flow_cr", "revenue_cagr_5yr",
            "pat_cagr_5yr", "composite_quality_score"
        ]

        stats_rows = []
        for metric in core_10_kpis:
            s = df[metric].dropna()
            if len(s) > 0:
                stats_rows.append({
                    "metric": metric,
                    "count": len(s),
                    "mean": round(float(s.mean()), 2),
                    "std": round(float(s.std()), 2),
                    "p10": round(float(np.percentile(s, 10)), 2),
                    "p25": round(float(np.percentile(s, 25)), 2),
                    "p50_median": round(float(np.percentile(s, 50)), 2),
                    "p75": round(float(np.percentile(s, 75)), 2),
                    "p90": round(float(np.percentile(s, 90)), 2),
                })

        df_stats = pd.DataFrame(stats_rows)
        out_path = os.path.join(OUTPUT_DIR, "portfolio_stats.csv")
        df_stats.to_csv(out_path, index=False)
        logger.info("Saved portfolio statistics to %s", out_path)
        return df_stats

    def generate_outlier_report(self) -> pd.DataFrame:
        """Detect company-level metric outliers using sector-relative Z-score (|Z| > 3)."""
        df = self.load_latest_universe()
        metrics = ["return_on_equity_pct", "operating_profit_margin_pct", "debt_to_equity", "free_cash_flow_cr"]
        outlier_rows = []

        for sec, sec_group in df.groupby("broad_sector"):
            for m in metrics:
                s = sec_group[m].dropna()
                if len(s) >= 3:
                    mean = s.mean()
                    std = s.std()
                    if std > 0:
                        for _, row in sec_group.iterrows():
                            val = row[m]
                            if pd.notna(val):
                                z = (val - mean) / std
                                if abs(z) > 3.0:
                                    outlier_rows.append({
                                        "company_id": row["company_id"],
                                        "company_name": row["company_name"],
                                        "sector": sec,
                                        "metric": m,
                                        "value": val,
                                        "z_score": round(float(z), 2),
                                        "sector_mean": round(float(mean), 2),
                                        "sector_std": round(float(std), 2),
                                        "flag": "Outlier (|Z|>3)"
                                    })

        df_outliers = pd.DataFrame(outlier_rows)
        out_path = os.path.join(OUTPUT_DIR, "outlier_report.csv")
        df_outliers.to_csv(out_path, index=False)
        logger.info("Saved %d statistical outliers to %s", len(df_outliers), out_path)
        return df_outliers


if __name__ == "__main__":
    eng = StatisticalClusteringEngine()
    eng.perform_kmeans_clustering()
    eng.generate_correlation_matrix()
    eng.generate_portfolio_statistics()
    eng.generate_outlier_report()
