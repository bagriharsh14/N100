-- 10+ Exploratory SQL Queries for Nifty 100 Financial Intelligence Platform

-- Query 1: Data Coverage - Total companies loaded
SELECT COUNT(*) AS total_companies FROM companies;

-- Query 2: Year Distribution in P&L
SELECT year, COUNT(DISTINCT company_id) AS company_count
FROM profitandloss
GROUP BY year
ORDER BY year DESC;

-- Query 3: Multi-Year Coverage Check (Companies with >= 10 years of P&L)
SELECT company_id, COUNT(year) AS years_of_data
FROM profitandloss
GROUP BY company_id
HAVING years_of_data >= 10
ORDER BY years_of_data DESC;

-- Query 4: Top 10 ROE Companies (Latest Year)
SELECT r.company_id, c.company_name, r.return_on_equity_pct
FROM financial_ratios r
JOIN companies c ON r.company_id = c.id
WHERE r.year = (SELECT MAX(year) FROM financial_ratios)
ORDER BY r.return_on_equity_pct DESC
LIMIT 10;

-- Query 5: Debt-Free Companies in Latest Year
SELECT r.company_id, c.company_name, r.debt_to_equity
FROM financial_ratios r
JOIN companies c ON r.company_id = c.id
WHERE r.debt_to_equity = 0
  AND r.year = (SELECT MAX(year) FROM financial_ratios)
ORDER BY c.company_name ASC;

-- Query 6: Consistently Positive Free Cash Flow (5 consecutive years)
SELECT company_id, COUNT(*) AS positive_fcf_yrs
FROM financial_ratios
WHERE free_cash_flow_cr > 0
GROUP BY company_id
HAVING positive_fcf_yrs >= 5
ORDER BY positive_fcf_yrs DESC;

-- Query 7: Sector Median ROE and Valuation Multiples
SELECT s.broad_sector,
       COUNT(DISTINCT r.company_id) AS company_count,
       ROUND(AVG(r.return_on_equity_pct), 2) AS avg_roe,
       ROUND(AVG(r.net_profit_margin_pct), 2) AS avg_npm
FROM financial_ratios r
JOIN sectors s ON r.company_id = s.company_id
WHERE r.year = (SELECT MAX(year) FROM financial_ratios)
GROUP BY s.broad_sector
ORDER BY avg_roe DESC;

-- Query 8: High Growth Companies (Revenue CAGR > 15% over 5 years)
SELECT r.company_id, c.company_name, s.broad_sector, r.revenue_cagr_5yr
FROM financial_ratios r
JOIN companies c ON r.company_id = c.id
JOIN sectors s ON r.company_id = s.company_id
WHERE r.revenue_cagr_5yr > 15
  AND r.year = (SELECT MAX(year) FROM financial_ratios)
ORDER BY r.revenue_cagr_5yr DESC;

-- Query 9: Missing Annual Report Links by Company
SELECT c.id, c.company_name, 2024 - COUNT(d.Year) AS missing_years
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id AND d.Year >= 2015
GROUP BY c.id, c.company_name
HAVING missing_years > 2
ORDER BY missing_years DESC;

-- Query 10: Peer Group Rankings by ROE
SELECT p.peer_group_name, r.company_id, r.return_on_equity_pct,
       RANK() OVER (PARTITION BY p.peer_group_name ORDER BY r.return_on_equity_pct DESC) AS roe_rank
FROM financial_ratios r
JOIN peer_groups p ON r.company_id = p.company_id
WHERE r.year = (SELECT MAX(year) FROM financial_ratios);

-- Query 11: Capital Allocation Patterns Count
SELECT capital_allocation_pattern, COUNT(*) AS company_count
FROM financial_ratios
WHERE year = (SELECT MAX(year) FROM financial_ratios)
  AND capital_allocation_pattern IS NOT NULL
GROUP BY capital_allocation_pattern
ORDER BY company_count DESC;

-- Query 12: Foreign Key Consistency Check
SELECT 'PL Orphan Count' AS check_name, COUNT(*) AS issues FROM profitandloss WHERE company_id NOT IN (SELECT id FROM companies)
UNION ALL
SELECT 'BS Orphan Count', COUNT(*) FROM balancesheet WHERE company_id NOT IN (SELECT id FROM companies)
UNION ALL
SELECT 'CF Orphan Count', COUNT(*) FROM cashflow WHERE company_id NOT IN (SELECT id FROM companies);
