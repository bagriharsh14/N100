import os
import sys
import pandas as pd
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.dashboard.utils.db import get_all_companies, query_db

st.set_page_config(page_title="Annual Reports | Nifty 100", page_icon="📑", layout="wide")

st.title("📑 Annual Reports & Primary Document Repository")
st.markdown("Direct access to BSE India annual report filings across 2010–2024 for all 92 companies.")

df_co = get_all_companies()
names = (df_co["id"] + " — " + df_co["company_name"]).tolist()

selected_name = st.selectbox("Select Company:", names)
ticker = selected_name.split(" — ")[0]

docs_df = query_db("SELECT * FROM documents WHERE company_id = ? ORDER BY Year DESC", (ticker,))

if not docs_df.empty:
    st.subheader(f"Annual Report Filings for {selected_name} ({len(docs_df)} Years Available)")
    
    for _, row in docs_df.iterrows():
        yr = row["Year"]
        url = row["Annual_Report"]
        is_valid = row.get("is_url_valid", 1)
        
        col1, col2, col3 = st.columns([1, 4, 2])
        col1.markdown(f"**FY {yr}**")
        col2.markdown(f"`{url}`" if url else "URL not recorded")
        if url:
            col3.markdown(f"[🔗 Open Annual Report PDF]({url})")
        else:
            col3.caption("Not available")
else:
    st.info(f"No annual report links indexed for {ticker}.")
