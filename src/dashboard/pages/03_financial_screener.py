import io
import os
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.analytics.screener.engine import ScreenerEngine

st.set_page_config(page_title="Investment Screener | Nifty 100", page_icon="🔍", layout="wide")

st.title("🔍 Multi-Criteria Investment Screener")
st.markdown("Filter and rank 92 Nifty 100 companies using quantitative presets or customizable slider parameters.")

engine = ScreenerEngine()
presets_dict = engine.config.get("presets", {})

preset_options = ["Custom Filter"] + [p["name"] for p in presets_dict.values()]
selected_preset_name = st.selectbox("Choose a Pre-Built Strategy or Custom Screen:", preset_options)

df_universe = engine.get_latest_data()

# Sidebar / Custom Controls
st.sidebar.header("🎯 Filter Parameters")
sectors_list = ["All"] + sorted(df_universe["broad_sector"].dropna().unique().tolist())
selected_sector = st.sidebar.selectbox("Sector Filter:", sectors_list)

min_roe = st.sidebar.slider("Min ROE (%)", min_value=-20.0, max_value=60.0, value=15.0 if selected_preset_name == "Custom Filter" else -20.0, step=1.0)
max_de = st.sidebar.slider("Max Debt to Equity (x)", min_value=0.0, max_value=10.0, value=2.0 if selected_preset_name == "Custom Filter" else 10.0, step=0.1)
min_fcf = st.sidebar.number_input("Min Free Cash Flow (₹ Cr)", value=0.0 if selected_preset_name == "Custom Filter" else -50000.0, step=500.0)
min_rev_cagr = st.sidebar.slider("Min 5-Yr Rev CAGR (%)", min_value=-20.0, max_value=50.0, value=10.0 if selected_preset_name == "Custom Filter" else -20.0, step=1.0)
max_pe = st.sidebar.slider("Max P/E Multiple (x)", min_value=5.0, max_value=100.0, value=60.0, step=1.0)

# Run Selected Filter
if selected_preset_name != "Custom Filter":
    # Find matching key
    pkey = next((k for k, v in presets_dict.items() if v.get("name") == selected_preset_name), "quality_compounder")
    df_results = engine.run_preset(pkey, df_universe)
    if selected_sector != "All":
        df_results = df_results[df_results["broad_sector"] == selected_sector]
else:
    df_results = engine.run_custom_filter(
        min_roe=min_roe,
        max_de=max_de,
        min_fcf=min_fcf if min_fcf != -50000.0 else None,
        sector=selected_sector if selected_sector != "All" else None,
        min_rev_cagr_5yr=min_rev_cagr if min_rev_cagr != -20.0 else None,
        max_pe=max_pe,
        df=df_universe
    )

st.subheader(f"Results: {len(df_results)} Matching Companies")

# Display and Export
cols_to_show = [
    "ticker", "company_name", "broad_sector", "return_on_equity_pct", "roce_pct",
    "net_profit_margin_pct", "debt_to_equity", "revenue_cagr_5yr", "free_cash_flow_cr",
    "pe_ratio", "pb_ratio", "dividend_yield_pct", "capital_allocation_pattern", "composite_quality_score"
]
available_cols = [c for c in cols_to_show if c in df_results.columns]

st.dataframe(df_results[available_cols], use_container_width=True, hide_index=True)

# Export buttons
col_exp1, col_exp2 = st.columns([1, 4])
with col_exp1:
    csv_data = df_results[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Results (CSV)",
        data=csv_data,
        file_name="screener_results.csv",
        mime="text/csv",
        use_container_width=True
    )
