import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.charts import create_trend_line_chart
from src.dashboard.utils.db import get_all_companies, query_db

st.set_page_config(page_title="Company Profile | Nifty 100", page_icon="🏢", layout="wide")

st.title("🏢 Company Intelligence Profile")
st.markdown("Deep fundamental teardown across 10-13 years of annual financial filings.")

df_co = get_all_companies()
tickers = df_co["id"].tolist()
names = (df_co["id"] + " — " + df_co["company_name"]).tolist()

selected_name = st.selectbox("Select Company:", names, index=names.index("TCS — Tata Consultancy Services Ltd") if "TCS — Tata Consultancy Services Ltd" in names else 0)
ticker = selected_name.split(" — ")[0]

# Query Company Data
with st.spinner("Loading company data..."):
    df_pl = query_db("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", (ticker,))
    df_bs = query_db("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", (ticker,))
    df_cf = query_db("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", (ticker,))
    df_r = query_db("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC", (ticker,))
    df_sec = query_db("SELECT * FROM sectors WHERE company_id = ?", (ticker,))
    df_pc = query_db("SELECT * FROM prosandcons WHERE company_id = ?", (ticker,))

if not df_r.empty:
    latest_r = df_r.iloc[-1]
    latest_pl = df_pl.iloc[-1] if not df_pl.empty else {}
    sec_info = df_sec.iloc[0] if not df_sec.empty else {}

    col_meta1, col_meta2 = st.columns([3, 1])
    with col_meta1:
        st.subheader(f"{selected_name}")
        st.caption(f"Sector: **{sec_info.get('broad_sector', 'N/A')}** | Sub-Sector: **{sec_info.get('sub_sector', 'N/A')}** | Cap: **{sec_info.get('market_cap_category', 'Large Cap')}**")
    with col_meta2:
        pdf_path = os.path.join("reports/tearsheets", f"{ticker}_tearsheet.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📄 Download 2-Page Tearsheet PDF",
                    data=f.read(),
                    file_name=f"{ticker}_tearsheet.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    # 6 KPI Tiles
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("ROE (Latest)", f"{latest_r.get('return_on_equity_pct', 0):.1f}%")
    c2.metric("ROCE (Latest)", f"{latest_r.get('roce_pct', 0):.1f}%")
    c3.metric("Net Margin (NPM)", f"{latest_r.get('net_profit_margin_pct', 0):.1f}%")
    c4.metric("Debt / Equity", f"{latest_r.get('debt_to_equity', 0):.2f}x")
    c5.metric("Free Cash Flow", f"₹{latest_r.get('free_cash_flow_cr', 0):,.0f} Cr")
    c6.metric("5-Yr Rev CAGR", f"{latest_r.get('revenue_cagr_5yr', 0):.1f}%")

    st.markdown("---")

    # Financial Charts
    tab1, tab2, tab3, tab4 = st.tabs(["📊 P&L Trends", "🏛️ Balance Sheet", "💵 Cash Flow", "🎯 Health & Radar"])
    
    with tab1:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_rev = px.bar(df_pl, x="year", y="sales", title="Revenue / Sales (₹ Crore)", color_discrete_sequence=["#1e3a8a"])
            st.plotly_chart(fig_rev, use_container_width=True)
        with col_t2:
            fig_pat = px.line(df_pl, x="year", y="net_profit", markers=True, title="Net Profit (PAT) (₹ Crore)", color_discrete_sequence=["#dc2626"])
            st.plotly_chart(fig_pat, use_container_width=True)
        st.dataframe(df_pl, use_container_width=True, hide_index=True)

    with tab2:
        if not df_bs.empty:
            fig_bs = px.bar(df_bs, x="year", y=["equity_capital", "reserves", "borrowings", "other_liabilities"], title="Balance Sheet Liabilities Composition (₹ Crore)", barmode="stack")
            st.plotly_chart(fig_bs, use_container_width=True)
            st.dataframe(df_bs, use_container_width=True, hide_index=True)

    with tab3:
        if not df_cf.empty:
            fig_cf = px.bar(df_cf, x="year", y=["operating_activity", "investing_activity", "financing_activity"], title="Cash Flow Breakdown (₹ Crore)", barmode="group")
            st.plotly_chart(fig_cf, use_container_width=True)
            st.dataframe(df_cf, use_container_width=True, hide_index=True)

    with tab4:
        col_rad, col_qc = st.columns([1, 1])
        with col_rad:
            radar_file = os.path.join("reports/radar_charts", f"{ticker}_radar.png")
            if os.path.exists(radar_file):
                st.image(radar_file, caption=f"{ticker} 8-Axis Radar Benchmark", use_container_width=True)
        with col_qc:
            st.markdown(f"### Composite Quality Score: **{latest_r.get('composite_quality_score', 0):.1f} / 100**")
            st.markdown(f"**Capital Allocation Pattern:** `{latest_r.get('capital_allocation_pattern', 'N/A')}`")
            
            # Pros and cons
            if os.path.exists("output/pros_cons_generated.csv"):
                df_pc_all = pd.read_csv("output/pros_cons_generated.csv")
                df_co_pc = df_pc_all[df_pc_all["company_id"] == ticker]
                pros = df_co_pc[df_co_pc["type"] == "pro"]["text"].tolist()
                cons = df_co_pc[df_co_pc["type"] == "con"]["text"].tolist()

                st.markdown("#### 🟢 Key Strengths (Pros)")
                for p in pros:
                    st.markdown(f"- {p}")
                st.markdown("#### 🔴 Key Considerations (Cons)")
                for c in cons:
                    st.markdown(f"- {c}")
