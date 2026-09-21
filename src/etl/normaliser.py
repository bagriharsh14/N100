import re
from typing import Any, Optional


def normalize_ticker(val: Any) -> str:
    """Normalize company ticker by trimming whitespace and converting to uppercase."""
    if val is None:
        return ""
    return str(val).strip().upper()


def normalize_year(val: Any) -> str:
    """Standardize diverse financial year notations to YYYY-MM format.
    
    Supports:
    - 'Mar-23', 'Mar 23', 'March-2023', 'Mar-2023' -> '2023-03'
    - 'FY23', 'FY 24' -> '2023-03', '2024-03'
    - 2023, '2023' -> '2023-03'
    - 'Dec-22', 'Jun-23' -> '2022-12', '2023-06'
    - '2023-03' -> '2023-03'
    - unparseable -> 'PARSE_ERROR'
    """
    if val is None:
        return "PARSE_ERROR"
    
    s = str(val).strip()
    if not s:
        return "PARSE_ERROR"

    # If already YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", s):
        return s

    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        "march": "03", "april": "04", "june": "06", "july": "07",
        "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"
    }

    # FY pattern: FY23, FY 24, FY2024
    m_fy = re.match(r"^FY\s*(\d{2,4})$", s, re.IGNORECASE)
    if m_fy:
        yr_str = m_fy.group(1)
        if len(yr_str) == 2:
            yr = 2000 + int(yr_str)
        else:
            yr = int(yr_str)
        return f"{yr:04d}-03"

    # Pure year integer: 2023, '2023' -> assume March FY
    if re.match(r"^\d{4}$", s):
        return f"{int(s):04d}-03"

    # Month-Year or Month Year: 'Mar-23', 'Mar 23', 'March-2023', 'Dec-22', 'Jun-23'
    m_my = re.match(r"^([A-Za-z]+)[-\s/]+(\d{2,4})$", s)
    if m_my:
        mon_str = m_my.group(1).lower()
        yr_str = m_my.group(2)
        if mon_str in month_map:
            mm = month_map[mon_str]
            if len(yr_str) == 2:
                yr = 2000 + int(yr_str)
            else:
                yr = int(yr_str)
            return f"{yr:04d}-{mm}"

    # Year-Month format: '2023/03'
    m_ym = re.match(r"^(\d{4})[-\s/]+(\d{1,2})$", s)
    if m_ym:
        yr = int(m_ym.group(1))
        mm = int(m_ym.group(2))
        return f"{yr:04d}-{mm:02d}"

    return "PARSE_ERROR"
