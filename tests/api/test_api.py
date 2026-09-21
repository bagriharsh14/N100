import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert data["db_row_counts"]["companies"] == 92


def test_companies_count():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92


def test_company_profile_valid():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TCS"
    assert "Tata" in data["company_name"]
    assert len(data["pros"]) >= 1
    assert len(data["cons"]) >= 1


def test_invalid_ticker_404():
    response = client.get("/api/v1/companies/INVALIDTICKERXYZ")
    assert response.status_code == 404


def test_screener_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for r in data:
        assert r["return_on_equity_pct"] >= 15.0


def test_sectors_list():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10


def test_sector_companies():
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_peer_group():
    response = client.get("/api/v1/peers/IT Services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_peer_compare():
    response = client.get("/api/v1/companies/TCS/peers/compare")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TCS"
    assert "company_metrics" in data


def test_market_cap():
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_company_documents():
    response = client.get("/api/v1/companies/TCS/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
