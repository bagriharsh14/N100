import datetime
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_latest_financial_ratios, query_db

st.set_page_config(page_title="Sector Analytics | Nifty 100", page_icon="🏭", layout="wide")

st.title("🏭 Macro & Industry Sector Analytics")
st.markdown("Sector rotation, relative positioning, and constituent benchmarking.")

df_universe = get_latest_financial_ratios()
sectors = sorted(df_universe["broad_sector"].dropna().unique().tolist())

selected_sector = st.selectbox("Select Macro Sector:", sectors)
df_sec = df_universe[df_universe["broad_sector"] == selected_sector]

# Sector PDF Download Link if available
clean_name = selected_sector.replace(" ", "_").replace("/", "_")
date_str = datetime.datetime.now().strftime("%Y%m%d")
sec_pdf_path = os.path.join("reports/sector", f"{clean_name}_report_{date_str}.pdf")

col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.subheader(f"{selected_sector} — Overview ({len(df_sec)} Constituents)")
with col_head2:
    if os.path.exists(sec_pdf_path):
        with open(sec_pdf_path, "rb") as f:
            st.download_button(
                label="📄 Download Sector PDF Report",
                data=f.read(),
                file_name=f"{clean_name}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# Bubble Chart: Sales vs ROE vs FCF
fig_bubble = px.scatter(
    df_sec,
    x="return_on_equity_pct",
    y="net_profit_margin_pct",
    size="sales",
    color="sub_sector",
    hover_name="ticker",
    text="ticker",
    title=f"{selected_sector}: ROE % vs Net Profit Margin (Bubble Size = Sales ₹ Cr)",
    labels={"return_on_equity_pct": "Return on Equity (%)", "net_profit_margin_pct": "Net Margin (%)"},
    template="plotly_white"
)
fig_bubble.update_traces(textposition="top center")
fig_bubble.update_layout(height=450)
st.plotly_chart(fig_bubble, use_container_width=True)

st.subheader("Sector Constituents Table")
cols_view = [
    "ticker", "company_name", "sub_sector", "return_on_equity_pct", "roce_pct",
    "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr",
    "pe_ratio", "composite_quality_score"
]
st.dataframe(df_sec[[c for c in cols_view if c in df_sec.columns]], use_container_width=True, hide_index=True)
