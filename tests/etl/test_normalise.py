import pytest
from src.etl.normaliser import normalize_ticker, normalize_year


def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"


def test_year_fy24():
    assert normalize_year("FY24") == "2024-03"


def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"


def test_year_garbage():
    assert normalize_year("xyz") == "PARSE_ERROR"


def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"


def test_year_march_2023():
    assert normalize_year("March-2023") == "2023-03"


def test_year_int_2023():
    assert normalize_year(2023) == "2023-03"


def test_year_str_2023():
    assert normalize_year("2023") == "2023-03"


def test_year_fy2024():
    assert normalize_year("FY2024") == "2024-03"


def test_year_jun23():
    assert normalize_year("Jun-23") == "2023-06"


def test_year_already_normalized():
    assert normalize_year("2023-03") == "2023-03"


def test_year_none():
    assert normalize_year(None) == "PARSE_ERROR"


def test_year_empty():
    assert normalize_year("") == "PARSE_ERROR"


def test_ticker_strip():
    assert normalize_ticker(" TCS ") == "TCS"


def test_ticker_lower():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_hyphen():
    assert normalize_ticker("bajaj-auto") == "BAJAJ-AUTO"


def test_ticker_ampersand():
    assert normalize_ticker("m&m") == "M&M"


def test_ticker_none():
    assert normalize_ticker(None) == ""


def test_ticker_upper():
    assert normalize_ticker("INFY") == "INFY"


def test_ticker_whitespace_tabs():
    assert normalize_ticker("\tHDFCBANK\n") == "HDFCBANK"
