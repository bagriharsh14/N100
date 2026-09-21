import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_all_companies, get_latest_financial_ratios, query_db

st.set_page_config(
    page_title="Nifty 100 Financial Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich executive styling
st.markdown("""
<style>
    .main-title { font-size: 26px; font-weight: 700; color: #1e3a8a; margin-bottom: 2px; }
    .sub-title { font-size: 13px; color: #64748b; margin-bottom: 16px; }
    .kpi-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center; }
    .kpi-title { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 20px; font-weight: 700; color: #1e3a8a; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📈 Nifty 100 Financial Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Production-grade fundamental analytics, screening, peer benchmarking & automated reporting for 92 Nifty 100 constituents.</div>', unsafe_allow_html=True)

# Top KPI Summary Cards
df_r = get_latest_financial_ratios()
df_co = get_all_companies()

if not df_r.empty:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Universe Size</div><div class="kpi-value">{len(df_r)} Cos</div></div>', unsafe_allow_html=True)
    with col2:
        med_roe = df_r["return_on_equity_pct"].median()
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Median ROE</div><div class="kpi-value">{med_roe:.1f}%</div></div>', unsafe_allow_html=True)
    with col3:
        med_roce = df_r["roce_pct"].median()
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Median ROCE</div><div class="kpi-value">{med_roce:.1f}%</div></div>', unsafe_allow_html=True)
    with col4:
        med_npm = df_r["net_profit_margin_pct"].median()
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Median NPM</div><div class="kpi-value">{med_npm:.1f}%</div></div>', unsafe_allow_html=True)
    with col5:
        med_de = df_r["debt_to_equity"].median()
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Median D/E</div><div class="kpi-value">{med_de:.2f}x</div></div>', unsafe_allow_html=True)
    with col6:
        med_pe = df_r["pe_ratio"].median()
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Median P/E (Sim)</div><div class="kpi-value">{med_pe:.1f}x</div></div>', unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

col_left, col_right = st.columns([1.2, 1.8])

with col_left:
    st.subheader("Sector Composition")
    sec_counts = df_r["broad_sector"].value_counts().reset_index()
    sec_counts.columns = ["Sector", "Companies"]
    fig_donut = px.pie(sec_counts, values="Companies", names="Sector", hole=0.45, color_discrete_sequence=px.colors.qualitative.Safe)
    fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=340)
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.subheader("Top 10 ROE Leaders in Nifty 100")
    top_roe = df_r.sort_values(by="return_on_equity_pct", ascending=False).head(10)
    fig_bar = px.bar(
        top_roe,
        x="ticker",
        y="return_on_equity_pct",
        color="broad_sector",
        text_auto=".1f",
        labels={"ticker": "Company Ticker", "return_on_equity_pct": "ROE %", "broad_sector": "Sector"},
        title="Leading Return on Equity (%)"
    )
    fig_bar.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=340, template="plotly_white")
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Nifty 100 Constituents Master Summary")
cols_view = ["ticker", "company_name", "broad_sector", "sub_sector", "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr", "pe_ratio", "composite_quality_score"]
st.dataframe(df_r[[c for c in cols_view if c in df_r.columns]], use_container_width=True, hide_index=True)
