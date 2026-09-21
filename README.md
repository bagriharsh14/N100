# 📊 Nifty 100 Financial Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF_Generation-darkred.svg)](https://www.reportlab.com/)
[![Tests](https://img.shields.io/badge/Pytest-78%20Passed-brightgreen.svg)](reports/pytest_report.html)
[![License](https://img.shields.io/badge/Classification-Internal%20Research-purple.svg)]()

> **An institutional-grade fundamental equity intelligence platform designed for equity research analysts, quantitative investors, and portfolio managers.**  
> Transform raw, disparate public filings across **92 Nifty 100 companies** and **10–13 years of annual history** into structured quantitative intelligence, automated institutional PDF tearsheets, multi-criteria screeners, and interactive visual dashboards — **100% self-contained with zero reliance on paid financial APIs.**

---

## 💡 What Is This Project & Why Does It Exist?

Analyzing the Indian equity large-cap universe (Nifty 100) across a decade of financial filings has historically required tedious manual data gathering from PDF annual reports, complex spreadsheet models prone to formula breakage, or expensive financial data terminals.

The **Nifty 100 Financial Intelligence Platform** solves this by establishing a **single, unified, and auditable source of truth**. It ingests Profit & Loss statements, Balance Sheets, Cash Flows, Sector Classifications, Market Capitalization histories, and Annual Report filings, and computes **50+ standardized financial KPIs** across profitability, solvency, efficiency, cash flow quality, and multi-year compounding growth.

### 🎯 Core Analytical Applications & Use Cases

| Persona / Use Case | How This Platform Empowers You |
|:---|:---|
| 💼 **Equity Research Analysts** | Instant company teardown with 2-page institutional tearsheets, 10-year trend visualizers, and automated rule-based pros/cons identifying operational moats and leverage risks. |
| 📊 **Quantitative Fund Managers** | Multi-parameter screener with 6 pre-built institutional strategies (*Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch*). |
| 🛡️ **Risk & Credit Analysts** | Early detection of cash flow distress (negative CFO funded by financing debt), working capital stretch, accrual quality degradation, and interest service coverage risks. |
| 🏭 **Sector & Portfolio Strategists** | Intra-sector benchmarking across 11 macro industries, 11 dedicated peer groups with within-group percentile ranking, and 8-axis radar comparison charts. |
| 💻 **Fintech & Algo Developers** | High-performance FastAPI REST server exposing 16 structured JSON endpoints and OpenAPI 3.0 documentation for quantitative backtesting pipelines. |

---

## 🌟 Key Capabilities & Feature Highlights

### 1. ⚙️ Automated 50+ KPI Financial Ratio Engine
- **Profitability & Margins:** Net Profit Margin (NPM), Operating Profit Margin (OPM), EBIT Margin, Return on Equity (ROE), Return on Capital Employed (ROCE), Return on Assets (ROA).
- **Leverage & Solvency:** Debt-to-Equity (D/E) with structural carve-outs for Financials/Banks, Interest Coverage Ratio (ICR) with debt-free substitution, Net Debt, Net Debt/EBITDA.
- **Cash Flow Intelligence:** Free Cash Flow (FCF), CapEx Intensity %, CFO/PAT Earnings Quality Ratio, FCF Conversion Rate %, FCF Yield %, and **8 Capital Allocation Sign Patterns** (e.g., *Reinvestor, Shareholder Returns, Distress Cash Burn*).
- **Longitudinal Growth (CAGR):** 3-Year, 5-Year, and 10-Year CAGRs for Revenue, Net Profit (PAT), and EPS — with explicit anomaly detection for base-year turnaround transitions (`base < 0` and `end > 0`).
- **Composite Financial Health Score (0–100):** Weighted multi-factor index combining Profitability (35%), Cash Quality (30%), Growth (20%), and Leverage (15%) with statistical P10/P90 winsorisation.

### 2. 🔍 Multi-Criteria Investment Screener
- **6 Pre-Built Investment Strategies:** Ready-to-use screens for compounders, deep value, momentum growth, dividend income, debt-free stalwarts, and turnaround candidates.
- **Custom Quantitative Filtering:** Adjust sliders for ROE, Debt/Equity, FCF, Revenue CAGR, and Valuation Multiples with live table updates and direct CSV/Excel export.
- **Sector-Relative Normalisation:** Eliminates structural biases (such as high D/E in banks or high P/E in consumer staples).

### 3. 👥 Peer Group Benchmarking & Radar Analytics
- **11 Dedicated Industry Peer Groups:** Private Banks, Public Banks, IT Services, Pharmaceuticals, Automobiles, Life Insurance, Oil & Gas, Power & Utilities, Steel & Metals, FMCG, and Consumer Finance.
- **Percentile Ranking Engine:** Calculates within-group percentile rank for 20 fundamental metrics.
- **8-Axis Radar Visualizations:** 92 company radar charts benchmarking individual performance against peer group median standards.

### 4. 📄 Institutional PDF & Excel Report Automation
- **92 Company Executive Tearsheets (`reports/tearsheets/`):** High-density, 2-page print-ready PDFs containing KPI scorecards, 10-year revenue/PAT charts, ROE/ROCE trends, balance sheet composition, cash flow tables, qualitative pros/cons, and embedded radar charts.
- **10+ Macro Sector Intelligence Reports (`reports/sector/`):** Comprehensive sector medians, dispersion metrics, and constituent leaderboards.
- **93-Page Master Portfolio Almanac (`reports/portfolio/`):** A unified compendium profiling all 92 companies with macroeconomic health summaries.
- **12-Page Analyst User Guide (`docs/analyst_guide.pdf`):** In-depth handbook detailing data lineage, formula references, dashboard navigation, and API integration.

### 5. 🖥️ Interactive 8-Screen Streamlit Dashboard
- **Screen 01 (Home / Overview):** Macro universe health banner, sector donut composition, and ROE leaderboards.
- **Screen 02 (Company Profile):** Deep-dive company teardown with searchable tickers, interactive P&L/BS/CF charts, and one-click tearsheet PDF download.
- **Screen 03 (Financial Screener):** Live strategy presets and multi-slider quantitative filter matrix.
- **Screen 04 (Peer Comparison):** Intra-group metrics comparison and radar overlay.
- **Screen 05 (Trend Analysis):** Multi-metric historical overlays (up to 3 concurrent metrics) and sparklines.
- **Screen 06 (Sector Analysis):** Interactive bubble charts (Revenue vs. ROE vs. Margins) and sector distribution tables.
- **Screen 07 (Capital Allocation Map):** Interactive treemap visualizing company cash flow deployment patterns across the Nifty 100.
- **Screen 08 (Annual Reports):** Indexed repository of 1,585 direct BSE annual report filing links.

---

## 🚀 Quick-Start Guide (< 5 Minutes)

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Git & Make (optional, but recommended)

### Step 1: Clone & Setup Environment
```bash
# Navigate to project folder
cd N100

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.venv\Scripts\activate          # On Windows (PowerShell / Command Prompt)

# Install pinned dependencies
pip install -r requirements.txt

# Configure environment variables
cp config/.env.template .env
```

### Step 2: Build Database & Compute Ratios
```bash
# 1. Ingest, validate (16 DQ rules), and populate SQLite database
make load

# 2. Compute 50+ KPIs, CAGRs, capital allocation matrix, and health scores
make ratios
```

### Step 3: Launch User Interfaces
```bash
# Launch interactive Streamlit analytics dashboard (opens on http://localhost:8501)
make dashboard

# Launch FastAPI REST server with OpenAPI Swagger UI (opens on http://localhost:8000/docs)
make api
```

### Step 4: Run Test Suite & Generate Reports
```bash
# Run 78 automated pytest tests (ETL, KPIs, DQ, REST API)
make test

# Generate all 92 tearsheets, 10 sector reports, and master portfolio PDF
make report
```

---

## 🛠️ Complete Makefile Command Reference

| Command | Action | Output / Description |
|:---|:---|:---|
| `make load` | Runs ETL pipeline | Loads 12 Excel files into `data/nifty100.db`, outputs `load_audit.csv` and `validation_failures.csv`. |
| `make ratios` | Executes Analytics Engine | Populates `financial_ratios`, generates `capital_allocation.csv`, `peer_comparison.xlsx`, `valuation_summary.xlsx`, `cashflow_intelligence.xlsx`, `pros_cons_generated.csv`, and `cluster_labels.csv`. |
| `make test` | Runs Pytest Suite | Executes 78 unit & integration tests and generates `reports/pytest_report.html`. |
| `make report` | PDF Reporting Suite | Compiles 92 company tearsheets, 10 sector intelligence reports, master portfolio PDF, and analyst guide. |
| `make dashboard`| Starts Web App | Launches multi-page Streamlit dashboard on port `8501`. |
| `make api` | Starts REST Server | Launches FastAPI ASGI server on port `8000`. |
| `make clean` | Workspace Maintenance | Purges `__pycache__` and temporary test caches while keeping database and outputs intact. |

---

## 📁 Project Architecture & Directory Layout

```
N100/
├── config/
│   ├── .env.template                   # Environment template
│   ├── logging_config.yaml             # Python logging configuration
│   └── screener_config.yaml            # D-08: Screener strategies and weights
├── data/
│   ├── raw/                            # 7 core Excel files (READ-ONLY public filings)
│   ├── supporting/                     # 5 supplementary Excel files (Sectors, Prices, MCAP, Peers)
│   └── nifty100.db                     # D-01: SQLite warehouse with 10 tables + FK integrity
├── docs/
│   ├── Nifty100_Project_Document_FINAL.pdf # Original project specification
│   ├── analyst_guide.pdf               # D-22: 12-page comprehensive user guide
│   ├── openapi.json                    # OpenAPI 3.0 specification
│   ├── postman_collection.json         # Ready-to-import Postman API collection
│   └── acceptance_checklist.pdf        # D-23: Signed acceptance record
├── notebooks/
│   └── exploratory_queries.sql         # D-04: 12 analytical SQL queries
├── output/
│   ├── load_audit.csv                  # D-02: Table-level ETL ingestion row counts
│   ├── validation_failures.csv         # D-03: 16 Data Quality rule audit logs
│   ├── capital_allocation.csv          # D-06: 8 cash flow patterns across 92 companies
│   ├── screener_output.xlsx            # D-07: 6 strategy preset results
│   ├── peer_comparison.xlsx            # D-09: 11 peer group sheets with percentiles
│   ├── valuation_summary.xlsx          # D-12: Multiples, medians and caution/discount flags
│   ├── valuation_flags.csv             # Granular valuation exception flags
│   ├── cashflow_intelligence.xlsx      # D-13: CFO quality scores & FCF compounding
│   ├── distress_alerts.csv             # Early warning cash flow distress flags
│   ├── pros_cons_generated.csv         # D-14: Rule-based pros & cons for all 92 companies
│   ├── analysis_parsed.csv             # D-15: Parsed growth text metrics
│   ├── cluster_labels.csv              # D-19: 5 statistical KMeans clusters
│   ├── portfolio_stats.csv             # P10–P90 statistical distributions for core KPIs
│   ├── outlier_report.csv              # Sector-relative Z-score outliers (|Z| > 3)
│   └── correlation_heatmap.png         # Pearson correlation heatmap
├── reports/
│   ├── tearsheets/                     # D-16: 92 individual 2-page company PDFs (>120KB each)
│   ├── sector/                         # D-17: Sector intelligence PDFs
│   ├── portfolio/                      # D-18: 93-page master portfolio summary PDF
│   ├── radar_charts/                   # D-10: 92 8-axis company radar PNGs
│   └── pytest_report.html              # D-21: 78 passing tests report
├── src/
│   ├── analytics/                      # Ratios, CAGR, Screener, Peer, Valuation, Clustering
│   ├── api/                            # D-20: FastAPI server with 16 endpoints
│   ├── dashboard/                      # D-11: Streamlit 8-screen application
│   ├── etl/                            # Loader, Normaliser, Validator, Schema
│   ├── nlp/                            # Analysis Parser, Pros/Cons Generator
│   └── reports/                        # ReportLab PDF Report Generators
├── tests/
│   ├── api/                            # API integration tests
│   ├── dq/                             # 16 DQ validation tests
│   ├── etl/                            # ETL normalisation & loader tests
│   ├── kpi/                            # Financial ratio & CAGR tests
│   └── conftest.py                     # Pytest root configuration
├── .env
├── Makefile
├── README.md
└── requirements.txt
```

---

## 📊 23 Mandatory Deliverables Tracker

| # | Deliverable | Format | Location | Status |
|---|---|---|---|---|
| **D-01** | SQLite Database | SQLite | `data/nifty100.db` | ✅ **VERIFIED (100%)** |
| **D-02** | ETL Load Audit | CSV | `output/load_audit.csv` | ✅ **VERIFIED (100%)** |
| **D-03** | DQ Validation Failures | CSV | `output/validation_failures.csv` | ✅ **VERIFIED (100%)** |
| **D-04** | Exploratory SQL Queries | SQL | `notebooks/exploratory_queries.sql` | ✅ **VERIFIED (100%)** |
| **D-05** | Financial Ratios Table | SQLite Table | `data/nifty100.db -> financial_ratios` | ✅ **VERIFIED (100%)** |
| **D-06** | Capital Allocation Matrix | CSV | `output/capital_allocation.csv` | ✅ **VERIFIED (100%)** |
| **D-07** | Screener Output Workbook | Excel | `output/screener_output.xlsx` | ✅ **VERIFIED (100%)** |
| **D-08** | Screener Configuration | YAML | `config/screener_config.yaml` | ✅ **VERIFIED (100%)** |
| **D-09** | Peer Comparison Workbook | Excel | `output/peer_comparison.xlsx` | ✅ **VERIFIED (100%)** |
| **D-10** | Radar Charts (92 PNGs) | PNG | `reports/radar_charts/` | ✅ **VERIFIED (100%)** |
| **D-11** | Streamlit Dashboard (8 Screens) | Web App | `src/dashboard/app.py` | ✅ **VERIFIED (100%)** |
| **D-12** | Valuation Summary | Excel | `output/valuation_summary.xlsx` | ✅ **VERIFIED (100%)** |
| **D-13** | Cash Flow Intelligence | Excel | `output/cashflow_intelligence.xlsx` | ✅ **VERIFIED (100%)** |
| **D-14** | Generated Pros & Cons | CSV | `output/pros_cons_generated.csv` | ✅ **VERIFIED (100%)** |
| **D-15** | Parsed Analysis CAGR | CSV | `output/analysis_parsed.csv` | ✅ **VERIFIED (100%)** |
| **D-16** | Company Tearsheets (92 PDFs) | PDF | `reports/tearsheets/` | ✅ **VERIFIED (100%)** |
| **D-17** | Sector Reports (10 PDFs) | PDF | `reports/sector/` | ✅ **VERIFIED (100%)** |
| **D-18** | Portfolio Summary PDF | PDF | `reports/portfolio/` | ✅ **VERIFIED (100%)** |
| **D-19** | Statistical Cluster Labels | CSV | `output/cluster_labels.csv` | ✅ **VERIFIED (100%)** |
| **D-20** | FastAPI Server (16 Endpoints) | Python API | `src/api/main.py` | ✅ **VERIFIED (100%)** |
| **D-21** | Pytest HTML Test Report | HTML | `reports/pytest_report.html` | ✅ **VERIFIED (100%)** |
| **D-22** | Analyst User Guide (12 Pages) | PDF | `docs/analyst_guide.pdf` | ✅ **VERIFIED (100%)** |
| **D-23** | Acceptance Checklist Signed | PDF | `docs/acceptance_checklist.pdf` | ✅ **VERIFIED (100%)** |

---

## 🏆 20 Quality Gates (Acceptance Criteria Verified)

- **AC-01 (Data Coverage):** 92 companies present in `companies` table.
- **AC-02 (Time Coverage):** >= 90% of companies have >= 10 years of financial statement records.
- **AC-03 (Schema Integrity):** All FK relationships intact (`PRAGMA foreign_key_check` returns 0 rows).
- **AC-04 (KPI Completeness):** `financial_ratios` table populated with 1,070 rows across all KPIs.
- **AC-05 (CAGR Accuracy):** Revenue CAGRs verified and turnaround logic handled (`base < 0` and `end > 0`).
- **AC-06 (ROE Accuracy):** ROE values verified against source filings.
- **AC-07 (Screener Accuracy):** Quality preset screener returns 22 companies (within 10–50 required range).
- **AC-08 (Dashboard Load):** Fast loading time (< 1s on localhost).
- **AC-09 (Dashboard Export):** Screener and data tables provide valid CSV/Excel downloads.
- **AC-10 (PDF Quality):** Institutional typography, zero text clipping or page overflow in any PDF report.
- **AC-11 (API Health):** `GET /api/v1/health` returns HTTP 200 with DB row counts.
- **AC-12 (API Accuracy):** `GET /api/v1/companies/TCS/ratios` returns full 12-year history.
- **AC-13 (API Screener):** `GET /api/v1/screener` outputs match Module 3 screener results.
- **AC-14 (Peer Coverage):** 11 peer groups with percentile rankings populated.
- **AC-15 (Cluster Coverage):** All 92 companies assigned to clusters 0–4 with 0 nulls.
- **AC-16 (NLP Coverage):** `pros_cons_generated.csv` contains >= 1 pro & >= 1 con for all 92 companies.
- **AC-17 (Report Coverage):** 92 tearsheet PDFs generated in `reports/tearsheets/` (each > 120KB).
- **AC-18 (Test Coverage):** 78 pytest tests passing with 0 failures and 0 errors.
- **AC-19 (DQ Documentation):** `output/validation_failures.csv` comprehensively documents all 16 checks.
- **AC-20 (Documentation):** `docs/analyst_guide.pdf` is 12 pages (>= 10 pages).

---

## 🌐 FastAPI REST Endpoints Reference (16 Endpoints)

| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/v1/companies` | `GET` | List all 92 companies with sector filter and search query (`?sector=`, `?search=`). |
| `/api/v1/companies/{ticker}` | `GET` | Full company profile with master fields, latest KPIs, and pros/cons. |
| `/api/v1/companies/{ticker}/pl` | `GET` | Historical Profit & Loss statement records (`?from_year=`, `?to_year=`). |
| `/api/v1/companies/{ticker}/bs` | `GET` | Historical Balance Sheet statement records (`?from_year=`, `?to_year=`). |
| `/api/v1/companies/{ticker}/cashflow` | `GET` | Historical Cash Flow statement records (`?from_year=`, `?to_year=`). |
| `/api/v1/companies/{ticker}/ratios` | `GET` | All pre-computed financial ratios (`?year=`). |
| `/api/v1/companies/{ticker}/tearsheet` | `GET` | Binary PDF stream download of the 2-page tearsheet. |
| `/api/v1/screener` | `GET` | Multi-parameter stock screening and ranking (`?min_roe=`, `?max_de=`, etc.). |
| `/api/v1/sectors` | `GET` | List all macro sectors with constituent count and median KPIs. |
| `/api/v1/sectors/{sector}/companies` | `GET` | All companies in sector with top KPIs. |
| `/api/v1/peers/{group_name}` | `GET` | Member companies in peer group with percentile ranks. |
| `/api/v1/companies/{ticker}/peers/compare` | `GET` | 8-axis radar comparison data: company vs. peer median vs. benchmark. |
| `/api/v1/market-cap/{ticker}` | `GET` | Historical valuation multiples (P/E, P/B, EV/EBITDA, Div Yield). |
| `/api/v1/portfolio/stats` | `GET` | P10 to P90 statistical distributions for core KPIs across the Nifty 100. |
| `/api/v1/companies/{ticker}/documents` | `GET` | Annual report links and document metadata for a company. |
| `/api/v1/health` | `GET` | Server health check, DB row counts, and uptime. |

---

## 📜 Principles & Standards
- **Zero Black-Box Numbers:** Every insight is traceable to an exact mathematical formula, every formula to a database column, and every column to a public filing.
- **Zero Test Failures Policy:** All 78 tests must pass before commits.
- **Data Integrity:** All monetary figures are standardized in **Indian Rupees (INR Crore)** unless explicitly stated otherwise.
