-- SQLite Schema for Nifty 100 Financial Intelligence Platform
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(20) PRIMARY KEY,
    company_logo TEXT,
    company_name VARCHAR(255) NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER,
    company_id VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER,
    company_id VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER,
    company_id VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER,
    company_id VARCHAR(20) PRIMARY KEY,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER,
    company_id VARCHAR(20) NOT NULL,
    Year INTEGER NOT NULL,
    Annual_Report TEXT,
    is_url_valid INTEGER DEFAULT 1,
    PRIMARY KEY (company_id, Year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER,
    company_id VARCHAR(20) NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sectors (
    company_id VARCHAR(20) PRIMARY KEY,
    broad_sector TEXT NOT NULL,
    sub_sector TEXT NOT NULL,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id VARCHAR(20) NOT NULL,
    date VARCHAR(10) NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    adjusted_close REAL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS market_cap (
    company_id VARCHAR(20) NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT NOT NULL,
    company_id VARCHAR(20) NOT NULL,
    is_benchmark INTEGER DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id VARCHAR(20) NOT NULL,
    year VARCHAR(10) NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    ebit_margin_pct REAL,
    return_on_equity_pct REAL,
    roce_pct REAL,
    return_on_assets_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    net_debt_cr REAL,
    net_debt_to_ebitda REAL,
    asset_turnover REAL,
    fixed_asset_turnover REAL,
    working_capital_days REAL,
    revenue_cagr_3yr REAL,
    revenue_cagr_5yr REAL,
    revenue_cagr_10yr REAL,
    pat_cagr_3yr REAL,
    pat_cagr_5yr REAL,
    eps_cagr_5yr REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    cfo_pat_ratio REAL,
    capex_intensity_pct REAL,
    fcf_conversion_rate_pct REAL,
    fcf_yield_pct REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    dividend_payout_ratio_pct REAL,
    book_value_per_share REAL,
    earnings_per_share REAL,
    capital_allocation_pattern TEXT,
    composite_quality_score REAL,
    cagr_flag TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS peer_percentiles (
    company_id VARCHAR(20) NOT NULL,
    peer_group_name TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    percentile_rank REAL,
    year VARCHAR(10),
    PRIMARY KEY (company_id, peer_group_name, metric, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
