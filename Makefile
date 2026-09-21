# Makefile for Nifty 100 Financial Intelligence Platform

.PHONY: load ratios test report dashboard api clean all

all: load ratios test report

# Step 1: Run ETL pipeline to load and validate all 12 datasets into SQLite
load:
	python src/etl/loader.py

# Step 2: Compute 50+ KPIs, capital allocation matrix, and populate financial_ratios table
ratios:
	python src/analytics/ratios.py
	python src/analytics/peer.py
	python src/analytics/valuation.py
	python src/analytics/clustering.py
	python src/nlp/parser.py
	python src/nlp/pros_cons_generator.py

# Step 3: Run full pytest test suite (78 tests) and generate HTML report
test:
	pytest tests/ --html=reports/pytest_report.html --self-contained-html

# Step 4: Generate all PDF reports (92 tearsheets, 11 sector reports, 1 portfolio summary)
report:
	python src/reports/portfolio_report.py
	python src/reports/analyst_guide.py
	python src/reports/acceptance_checklist.py

# Step 5: Start Streamlit multi-page dashboard on port 8501
dashboard:
	streamlit run src/dashboard/app.py --server.port 8501

# Step 6: Start FastAPI server on port 8000
api:
	uvicorn src.api.main:app --port 8000 --reload

# Step 7: Clean cache and temporary test artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
