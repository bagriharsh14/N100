import pytest
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    get_capex_intensity_label,
    get_cfo_quality_badge,
)


def test_roe_positive():
    net_profit = 100.0
    equity = 500.0
    roe = (net_profit / equity * 100.0) if equity > 0 else None
    assert roe == 20.0


def test_roe_neg_equity():
    net_profit = 100.0
    equity = -50.0
    roe = (net_profit / equity * 100.0) if equity > 0 else None
    assert roe is None


def test_de_debtfree():
    borrowings = 0.0
    equity = 500.0
    de = (borrowings / equity) if equity > 0 else None
    assert de == 0.0


def test_icr_debtfree():
    op_profit = 100.0
    interest = 0.0
    icr = (op_profit / interest) if interest > 0 else None
    assert icr is None


def test_cagr_turnaround():
    cagr_val, flag, disp = calculate_cagr(-100.0, 200.0, 5)
    assert cagr_val is None
    assert flag == "TURNAROUND"
    assert "Turnaround" in disp


def test_cagr_normal():
    # 100 * (1.10)^5 = 161.051
    cagr_val, flag, disp = calculate_cagr(100.0, 161.051, 5)
    assert cagr_val == 10.0
    assert flag == "NORMAL"


def test_cagr_zero_base():
    cagr_val, flag, disp = calculate_cagr(0.0, 100.0, 5)
    assert cagr_val is None
    assert flag == "ZERO_BASE"


def test_cagr_both_negative():
    cagr_val, flag, disp = calculate_cagr(-100.0, -50.0, 5)
    assert cagr_val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_decline_to_loss():
    cagr_val, flag, disp = calculate_cagr(100.0, -50.0, 5)
    assert cagr_val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_insufficient():
    cagr_val, flag, disp = calculate_cagr(100.0, 120.0, 0)
    assert cagr_val is None
    assert flag == "INSUFFICIENT"


def test_cfo_quality_high():
    assert get_cfo_quality_badge(1.2) == "High Quality Earnings"


def test_cfo_quality_accrual_risk():
    assert get_cfo_quality_badge(0.3) == "Accrual Risk"


def test_capex_intensity_light():
    assert get_capex_intensity_label(2.0) == "Asset-Light (<3%)"


def test_capex_intensity_heavy():
    assert get_capex_intensity_label(12.0) == "Capital Intensive (>8%)"


def test_capital_allocation_reinvestor():
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(100, -50, -30, cfo_pat_ratio=0.8)
    assert (s_cfo, s_cfi, s_cff) == ("+", "-", "-")
    assert label == "Reinvestor"


def test_capital_allocation_shareholder_returns():
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(100, -30, -50, cfo_pat_ratio=1.4)
    assert (s_cfo, s_cfi, s_cff) == ("+", "-", "-")
    assert label == "Shareholder Returns"


def test_capital_allocation_distress():
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(-50, -20, 100)
    assert (s_cfo, s_cfi, s_cff) == ("-", "-", "+")
    assert "Distress" in label


def test_net_profit_margin():
    sales = 1000.0
    net_profit = 150.0
    npm = (net_profit / sales * 100.0) if sales > 0 else None
    assert npm == 15.0


def test_opm_formula():
    sales = 1000.0
    operating_profit = 250.0
    opm = (operating_profit / sales * 100.0) if sales > 0 else None
    assert opm == 25.0


def test_free_cash_flow():
    cfo = 500.0
    cfi = -200.0
    fcf = cfo + cfi
    assert fcf == 300.0
