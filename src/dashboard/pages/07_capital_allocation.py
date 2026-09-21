import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_latest_financial_ratios, query_db

st.set_page_config(page_title="Capital Allocation | Nifty 100", page_icon="🗺️", layout="wide")

st.title("🗺️ Capital Allocation & Cash Flow Intelligence")
st.markdown("Analyze how Nifty 100 companies allocate operating cash flows across reinvestment, debt service, and shareholder returns.")

df_universe = get_latest_financial_ratios()

# Distribution across 8 capital allocation classes
cap_counts = df_universe["capital_allocation_pattern"].value_counts().reset_index()
cap_counts.columns = ["Pattern", "Companies"]

col_tree, col_bar = st.columns([1.5, 1])

with col_tree:
    fig_tree = px.treemap(
        df_universe,
        path=["capital_allocation_pattern", "broad_sector", "ticker"],
        values="sales",
        color="composite_quality_score",
        color_continuous_scale="Blues",
        title="Capital Allocation Structure Treemap (Tile Size = Sales ₹ Cr)"
    )
    fig_tree.update_layout(height=450, margin=dict(t=30, l=10, r=10, b=10))
    st.plotly_chart(fig_tree, use_container_width=True)

with col_bar:
    fig_bar = px.bar(
        cap_counts,
        x="Companies",
        y="Pattern",
        orientation="h",
        text="Companies",
        title="Company Count by Allocation Pattern",
        color="Pattern",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_bar.update_layout(height=450, showlegend=False, margin=dict(t=30, l=10, r=10, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Capital Allocation Drill-Down")
selected_pattern = st.selectbox("Filter by Pattern:", ["All"] + cap_counts["Pattern"].tolist())

if selected_pattern != "All":
    df_filtered = df_universe[df_universe["capital_allocation_pattern"] == selected_pattern]
else:
    df_filtered = df_universe

cols_cap = [
    "ticker", "company_name", "broad_sector", "capital_allocation_pattern",
    "free_cash_flow_cr", "return_on_equity_pct", "debt_to_equity", "composite_quality_score"
]
st.dataframe(df_filtered[[c for c in cols_cap if c in df_filtered.columns]], use_container_width=True, hide_index=True)
