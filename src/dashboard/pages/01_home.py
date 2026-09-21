import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_all_companies, get_latest_financial_ratios

st.set_page_config(page_title="Home / Overview | Nifty 100", page_icon="📈", layout="wide")

st.title("📈 Nifty 100 Macro Overview & Market Health")
st.markdown("Macroeconomic aggregate intelligence, sector compositions, and key profitability metrics.")

df_r = get_latest_financial_ratios()

if not df_r.empty:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Universe Size", f"{len(df_r)} Cos")
    c2.metric("Median ROE", f"{df_r['return_on_equity_pct'].median():.1f}%")
    c3.metric("Median ROCE", f"{df_r['roce_pct'].median():.1f}%")
    c4.metric("Median NPM", f"{df_r['net_profit_margin_pct'].median():.1f}%")
    c5.metric("Median D/E", f"{df_r['debt_to_equity'].median():.2f}x")
    c6.metric("Median P/E (Sim)", f"{df_r['pe_ratio'].median():.1f}x")

    st.markdown("<br/>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1.8])
    with col1:
        st.subheader("Sector Composition")
        sec_counts = df_r["broad_sector"].value_counts().reset_index()
        sec_counts.columns = ["Sector", "Companies"]
        fig_donut = px.pie(sec_counts, values="Companies", names="Sector", hole=0.45, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=340)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        st.subheader("Top 10 ROE Leaders")
        top_roe = df_r.sort_values(by="return_on_equity_pct", ascending=False).head(10)
        fig_bar = px.bar(
            top_roe,
            x="ticker",
            y="return_on_equity_pct",
            color="broad_sector",
            text_auto=".1f",
            labels={"ticker": "Company", "return_on_equity_pct": "ROE %", "broad_sector": "Sector"}
        )
        fig_bar.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=340, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Nifty 100 Financial Universe")
    cols = ["ticker", "company_name", "broad_sector", "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr", "pe_ratio", "composite_quality_score"]
    st.dataframe(df_r[[c for c in cols if c in df_r.columns]], use_container_width=True, hide_index=True)
