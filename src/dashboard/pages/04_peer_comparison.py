import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import query_db

st.set_page_config(page_title="Peer Comparison | Nifty 100", page_icon="👥", layout="wide")

st.title("👥 Peer Group Benchmarking & Radar Analytics")
st.markdown("Compare industry peers across 20 financial metrics and relative percentile rankings.")

df_pg = query_db("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name")
peer_groups = df_pg["peer_group_name"].tolist()

selected_group = st.selectbox("Select Peer Group:", peer_groups)

# Query Members
q = """
WITH latest_years AS (
    SELECT company_id, MAX(year) AS max_year
    FROM financial_ratios
    GROUP BY company_id
)
SELECT 
    pg.company_id AS ticker,
    pg.is_benchmark,
    c.company_name,
    r.*
FROM peer_groups pg
JOIN latest_years ly ON pg.company_id = ly.company_id
JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
JOIN companies c ON pg.company_id = c.id
WHERE pg.peer_group_name = ?
ORDER BY r.return_on_equity_pct DESC
"""
df_members = query_db(q, (selected_group,))

if not df_members.empty:
    st.subheader(f"Peer Universe: {selected_group} ({len(df_members)} Companies)")
    
    # Radar Chart Selection
    col_rad1, col_rad2 = st.columns([1, 1])
    with col_rad1:
        member_tickers = df_members["ticker"].tolist()
        sel_co = st.selectbox("View Company Radar vs Group Median:", member_tickers)
        radar_img = os.path.join("reports/radar_charts", f"{sel_co}_radar.png")
        if os.path.exists(radar_img):
            st.image(radar_img, use_container_width=True)

    with col_rad2:
        st.markdown("### Peer Group Metrics Comparison")
        fig_bar = px.bar(
            df_members,
            x="ticker",
            y="return_on_equity_pct",
            color="is_benchmark",
            labels={"return_on_equity_pct": "ROE %", "ticker": "Company", "is_benchmark": "Is Benchmark"},
            title="Intra-Group Return on Equity (%)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detailed Comparison Table
    st.markdown("### Detailed Side-by-Side Financial Ratios")
    cols_peer = [
        "ticker", "company_name", "is_benchmark", "return_on_equity_pct", "roce_pct",
        "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr",
        "pe_ratio", "composite_quality_score"
    ]
    st.dataframe(df_members[[c for c in cols_peer if c in df_members.columns]], use_container_width=True, hide_index=True)
