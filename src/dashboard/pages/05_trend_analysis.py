import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_all_companies, query_db

st.set_page_config(page_title="Trend Analysis | Nifty 100", page_icon="📉", layout="wide")

st.title("📉 Multi-Year Trend & Growth Analytics")
st.markdown("Analyze longitudinal performance trends and overlay multiple KPIs over 10-13 years.")

df_co = get_all_companies()
tickers = df_co["id"].tolist()
names = (df_co["id"] + " — " + df_co["company_name"]).tolist()

sel_name = st.selectbox("Select Company to Inspect:", names)
ticker = sel_name.split(" — ")[0]

df_r = query_db("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC", (ticker,))
df_pl = query_db("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", (ticker,))

if not df_r.empty:
    merged = pd.merge(df_pl, df_r, on=["company_id", "year"], how="inner")

    available_metrics = [
        "sales", "operating_profit", "net_profit", "eps",
        "return_on_equity_pct", "roce_pct", "net_profit_margin_pct", "operating_profit_margin_pct",
        "debt_to_equity", "free_cash_flow_cr", "pe_ratio"
    ]
    valid_metrics = [m for m in available_metrics if m in merged.columns]

    selected_metrics = st.multiselect("Select KPIs to Overlay (Up to 3):", valid_metrics, default=["return_on_equity_pct", "roce_pct"])

    if selected_metrics:
        fig = go.Figure()
        for idx, m in enumerate(selected_metrics):
            fig.add_trace(go.Scatter(
                x=merged["year"],
                y=merged[m],
                mode="lines+markers",
                name=m.replace("_", " ").title(),
                line=dict(width=2.5)
            ))
        fig.update_layout(
            title=f"{ticker} — Multi-Year Trend Comparison",
            xaxis_title="Financial Year",
            yaxis_title="Metric Value",
            template="plotly_white",
            hovermode="x unified",
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Historical Statement and Ratio History")
    st.dataframe(merged, use_container_width=True, hide_index=True)
