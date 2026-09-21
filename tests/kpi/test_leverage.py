import pytest


def test_asset_turnover():
    sales = 5000.0
    total_assets = 2500.0
    turnover = sales / total_assets
    assert turnover == 2.0


def test_fixed_asset_turnover():
    sales = 3000.0
    fixed_assets = 1000.0
    fa_turn = sales / fixed_assets
    assert fa_turn == 3.0


def test_working_capital_days():
    sales = 3650.0
    other_assets = 500.0
    other_liabilities = 300.0
    wc_days = (other_assets - other_liabilities) / sales * 365.0
    assert wc_days == 20.0


def test_fcf_conversion_rate():
    fcf = 400.0
    operating_profit = 800.0
    fcf_conv = fcf / operating_profit * 100.0
    assert fcf_conv == 50.0


def test_book_value_per_share():
    total_equity = 10000.0
    equity_cap = 100.0
    face_val = 1.0
    shares = equity_cap / face_val
    bvps = total_equity / shares
    assert bvps == 100.0


def test_net_debt_calculation():
    borrowings = 1500.0
    investments = 500.0
    net_debt = borrowings - investments
    assert net_debt == 1000.0
