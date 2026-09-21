# Nifty 100 Financial Intelligence Platform 📈

An end-to-end financial data analytics and fundamental research platform built for analyzing **92 Nifty 100 companies** over **10–13 years** of historical financial data.

This project was built to make in-depth Indian equity fundamental analysis accessible and automated without relying on expensive financial data subscriptions. It includes an automated ETL pipeline, financial ratio computation engine, custom stock screener, peer comparison radar charts, automated PDF report generation, and an interactive multi-page web dashboard.

---

## 📌 Project Overview

Fundamental equity analysis usually requires manually digging through years of annual reports, cleaning messy balance sheets, and building financial models in Excel. 

This platform automates that entire process:
1. **Data Ingestion & Cleaning**: Ingests annual P&L statements, Balance Sheets, Cash Flows, Sector Classifications, and Price data into a relational SQLite database.
2. **Ratio Computation**: Automatically calculates **50+ financial ratios** (profitability, leverage, efficiency, growth CAGR, cash conversion, and composite health scores).
3. **Interactive Dashboard**: A multi-page Streamlit web app to search companies, screen stocks, overlay multi-year metrics, and view peer group comparisons.
4. **Automated Reporting**: Generates 2-page executive tearsheet PDFs for all 92 companies and sector intelligence reports.
5. **REST API**: Built with FastAPI to serve fundamental financial data via structured JSON endpoints.

---

## ✨ Features & Modules

### 1. Financial Ratio & KPI Engine
- **Profitability**: Net Profit Margin (NPM), Operating Profit Margin (OPM), Return on Equity (ROE), Return on Capital Employed (ROCE), and Return on Assets (ROA).
- **Leverage & Solvency**: Debt-to-Equity (with bank/NBFC adjustments), Interest Coverage Ratio, and Net Debt.
- **Cash Flow Quality**: Free Cash Flow (FCF), CapEx Intensity %, CFO/PAT earnings quality ratio, and cash flow sign pattern classification (*Reinvestor, Shareholder Returns, etc.*).
- **Long-term Growth**: 3-Year, 5-Year, and 10-Year CAGRs for Revenue, Profit, and EPS with turnaround logic handling.
- **Composite Quality Score**: A 0–100 overall score evaluating Profitability (35%), Cash Quality (30%), Growth (20%), and Leverage (15%).

### 2. Multi-Criteria Stock Screener
- **Pre-Built Strategy Screens**:
  - *Quality Compounders* (High ROE, low debt, positive FCF, steady revenue growth)
  - *Value Picks* (Low P/E, reasonable P/B, dividend paying)
  - *Growth Accelerators* (High 5-year profit and sales compounding)
  - *Dividend Champions* (High dividend yield, sustainable payout)
  - *Debt-Free Blue Chips* (Zero debt, high ROE, large scale)
  - *Turnaround Watch* (Accelerating revenue with positive cash flows)
- **Custom Filters**: Interactive sidebar sliders to screen by custom metrics with live table filtering and CSV export.

### 3. Peer Comparison & Radar Analytics
- Benchmarks companies against **11 industry peer groups** (*IT Services, Private Banks, Auto OEMs, Pharma, FMCG, etc.*).
- Generates **8-axis radar charts** comparing a company's financial profile against its peer group median.

### 4. Interactive Streamlit Dashboard
- **Home / Overview**: High-level market health metrics, sector distribution, and top ROE leaders.
- **Company Profile**: Deep teardown of any ticker with interactive 10-year P&L, Balance Sheet, and Cash Flow charts.
- **Financial Screener**: Live slider-based stock screener with downloadable results.
- **Peer Comparison**: Side-by-side KPI comparison and radar charts.
- **Trend Analysis**: Overlay up to 3 financial metrics over time.
- **Sector Analysis**: Interactive bubble charts (Revenue vs. ROE vs. Margin).
- **Capital Allocation Map**: Treemap showing how companies allocate cash.
- **Annual Reports**: Direct repository of annual report links.

### 5. Automated PDF Report Generation
- **Company Tearsheets**: 2-page executive PDF summaries for all 92 companies with scorecards, trend charts, and radar graphs.
- **Sector Intelligence Reports**: PDF reports summarizing sector medians and constituent metrics.
- **Portfolio Summary**: A combined multi-page reference document profiling all tracked companies.

### 6. FastAPI Backend Server
- 16 REST endpoints with auto-generated interactive OpenAPI / Swagger documentation at `/docs`.

---

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **Data & Analytics**: Pandas, NumPy, SciPy, Scikit-learn
- **Database**: SQLite 3 (relational schema with foreign key constraints)
- **Frontend / Dashboard**: Streamlit, Plotly
- **Backend / API**: FastAPI, Uvicorn, Pydantic
- **PDF Generation**: ReportLab, Matplotlib, Seaborn
- **Testing**: Pytest

---

## 🚀 How to Run Locally

### 1. Clone the Repository & Set Up Environment
```bash
# Clone the repository
git clone https://github.com/bagriharsh14/N100.git
cd N100

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Create .env file
cp config/.env.template .env
```

### 2. Build the Database & Run Analytics
```bash
# 1. Load and clean all datasets into SQLite
python src/etl/loader.py

# 2. Compute all financial ratios, CAGRs, and health scores
python src/analytics/ratios.py
python src/analytics/peer.py
python src/analytics/valuation.py
python src/analytics/clustering.py
python src/nlp/parser.py
python src/nlp/pros_cons_generator.py
```

### 3. Launch the Dashboard
```bash
streamlit run src/dashboard/app.py
```
Open your browser at **`http://localhost:8501`** to explore the dashboard.

### 4. Start the REST API (Optional)
```bash
uvicorn src.api.main:app --port 8000 --reload
```
Open **`http://localhost:8000/docs`** to test the interactive API endpoints.

### 5. Generate All PDF Reports (Optional)
```bash
python src/reports/portfolio_report.py
```
Generated reports will be saved in the `reports/` folder.

---

## 📂 Project Structure

```
N100/
├── config/
│   ├── .env.template          # Environment variables template
│   ├── logging_config.yaml    # Logging configuration
│   └── screener_config.yaml   # Screener filter rules and weights
├── data/
│   ├── raw/                   # Core public filings Excel datasets
│   ├── supporting/            # Sector mappings, stock prices, market cap
│   └── nifty100.db            # SQLite relational database
├── docs/
│   ├── analyst_guide.pdf      # Detailed user guide and formula manual
│   ├── openapi.json           # Exported OpenAPI 3.0 specification
│   ├── postman_collection.json# Postman API collection
│   └── acceptance_checklist.pdf# Project delivery summary
├── notebooks/
│   └── exploratory_queries.sql# Useful SQL analysis queries
├── output/                    # Exported Excel & CSV analytics outputs
├── reports/
│   ├── tearsheets/            # 2-page company tearsheet PDFs
│   ├── sector/                # Sector intelligence PDFs
│   ├── portfolio/             # Portfolio summary PDF
│   └── radar_charts/          # 8-axis company radar charts (PNG)
├── src/
│   ├── analytics/             # Ratios, CAGR, Screener, Peer, Valuation, Clustering
│   ├── api/                   # FastAPI routes and endpoints
│   ├── dashboard/             # Streamlit app and pages
│   ├── etl/                   # Data loader, normaliser, validator, schema
│   ├── nlp/                   # Text parsing & pros/cons generation
│   └── reports/               # PDF report generators (ReportLab)
├── tests/                     # Automated unit and API test suite
├── Makefile                   # Convenient make commands
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## 💡 What I Learned / Key Takeaways

- **Data Normalization & Cleaning**: Handling real-world data issues such as mixed fiscal year labels, inconsistent date formats, and missing values across financial statements.
- **Financial Engineering**: Implementing standard corporate finance formulas (ROE, ROCE, FCF, CAGR, working capital cycles) and handling mathematical edge cases like division-by-zero, debt-free companies, and base-year sign inversions.
- **Data Visualization & UX**: Designing interactive Streamlit pages with Plotly charts and automated PDF generation with ReportLab.
- **API Design**: Building modular REST endpoints in FastAPI with clean data models and parameter validation.

---

## 📬 Contact & Feedback

If you have any suggestions, questions, or ideas for improvement, feel free to reach out or open an issue!
