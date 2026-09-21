import pandas as pd
import pytest
from src.etl.validator import DataQualityValidator


def test_dq01_company_uniqueness():
    val = DataQualityValidator()
    df = pd.DataFrame([{"id": "TCS"}, {"id": "TCS"}])
    res = val.validate_companies(df)
    assert len(res) == 1
    assert any(f["rule_id"] == "DQ-01" for f in val.failures)


def test_dq02_annual_pk_uniqueness():
    val = DataQualityValidator()
    df = pd.DataFrame([
        {"company_id": "TCS", "year": "2023-03", "sales": 100, "expenses": 80, "operating_profit": 20, "opm_percentage": 20, "net_profit": 15},
        {"company_id": "TCS", "year": "2023-03", "sales": 110, "expenses": 85, "operating_profit": 25, "opm_percentage": 22.7, "net_profit": 18}
    ])
    res = val.validate_pl(df, {"TCS"})
    assert len(res) == 1
    assert any(f["rule_id"] == "DQ-02" for f in val.failures)


def test_dq03_fk_integrity():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "ORPHAN", "year": "2023-03"}])
    res = val.validate_pl(df, {"TCS"})
    assert len(res) == 0
    assert any(f["rule_id"] == "DQ-03" for f in val.failures)


def test_dq04_bs_balance():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "total_assets": 1000.0, "total_liabilities": 1050.0, "fixed_assets": 100.0}])
    res = val.validate_bs(df, {"TCS"})
    assert len(res) == 1
    assert any(f["rule_id"] == "DQ-04" for f in val.failures)


def test_dq05_opm_cross_check():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "sales": 100.0, "operating_profit": 20.0, "opm_percentage": 30.0}])
    res = val.validate_pl(df, {"TCS"})
    assert any(f["rule_id"] == "DQ-05" for f in val.failures)


def test_dq06_zero_sales():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "sales": 0.0, "operating_profit": 0.0, "opm_percentage": 0.0}])
    res = val.validate_pl(df, {"TCS"})
    assert any(f["rule_id"] == "DQ-06" for f in val.failures)


def test_dq07_year_format():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "PARSE_ERROR"}])
    res = val.validate_pl(df, {"TCS"})
    assert len(res) == 0
    assert any(f["rule_id"] == "DQ-07" for f in val.failures)


def test_dq08_ticker_format():
    val = DataQualityValidator()
    df = pd.DataFrame([{"id": "A"}, {"id": "VERYLONGINVALIDTICKERNAME"}])
    res = val.validate_companies(df)
    assert len(res) == 0
    assert any(f["rule_id"] == "DQ-08" for f in val.failures)


def test_dq09_net_cash_check():
    val = DataQualityValidator()
    df = pd.DataFrame([{
        "company_id": "TCS", "year": "2023-03",
        "operating_activity": 100.0, "investing_activity": -40.0, "financing_activity": -20.0,
        "net_cash_flow": 200.0
    }])
    res = val.validate_cf(df, {"TCS"})
    assert res.iloc[0]["net_cash_flow"] == 40.0
    assert any(f["rule_id"] == "DQ-09" for f in val.failures)


def test_dq10_non_negative_fixed_assets():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "total_assets": 100.0, "total_liabilities": 100.0, "fixed_assets": -50.0}])
    res = val.validate_bs(df, {"TCS"})
    assert res.iloc[0]["fixed_assets"] == 0.0
    assert any(f["rule_id"] == "DQ-10" for f in val.failures)


def test_dq11_tax_rate_range():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "sales": 100.0, "operating_profit": 20.0, "tax_percentage": 75.0}])
    res = val.validate_pl(df, {"TCS"})
    assert any(f["rule_id"] == "DQ-11" for f in val.failures)


def test_dq12_dividend_payout_cap():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "sales": 100.0, "operating_profit": 20.0, "dividend_payout": 250.0}])
    res = val.validate_pl(df, {"TCS"})
    assert any(f["rule_id"] == "DQ-12" for f in val.failures)


def test_dq14_eps_sign_consistency():
    val = DataQualityValidator()
    df = pd.DataFrame([{"company_id": "TCS", "year": "2023-03", "sales": 100.0, "operating_profit": 20.0, "net_profit": 50.0, "eps": -5.0}])
    res = val.validate_pl(df, {"TCS"})
    assert any(f["rule_id"] == "DQ-14" for f in val.failures)


def test_dq16_coverage_check():
    val = DataQualityValidator()
    pl_df = pd.DataFrame([{"company_id": "SHORT", "year": "2023-03"}, {"company_id": "SHORT", "year": "2024-03"}])
    val.validate_coverage(pl_df, {"SHORT"})
    assert any(f["rule_id"] == "DQ-16" for f in val.failures)
