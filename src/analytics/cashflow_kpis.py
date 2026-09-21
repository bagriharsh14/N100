from typing import Dict, Optional, Tuple


def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """Classify 8 capital allocation sign patterns.
    
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    cfo_val = float(cfo) if cfo is not None else 0.0
    cfi_val = float(cfi) if cfi is not None else 0.0
    cff_val = float(cff) if cff is not None else 0.0

    s_cfo = "+" if cfo_val >= 0 else "-"
    s_cfi = "+" if cfi_val >= 0 else "-"
    s_cff = "+" if cff_val >= 0 else "-"

    pattern = (s_cfo, s_cfi, s_cff)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "-", "+"):
        label = "Aggressive Expansion"
    elif pattern == ("+", "+", "-"):
        label = "Divesting / Debt Payoff"
    elif pattern == ("+", "+", "+"):
        label = "Capital Infusion"
    elif pattern == ("-", "-", "+"):
        label = "Distress Signal (Financing Ops)"
    elif pattern == ("-", "-", "-"):
        label = "Distress Signal (Cash Burn)"
    elif pattern == ("-", "+", "+"):
        label = "Asset Liquidation & Support"
    else:  # ("-", "+", "-")
        label = "Distress Signal (Severe Burn)"

    return s_cfo, s_cfi, s_cff, label


def get_cfo_quality_badge(cfo_pat_ratio: Optional[float]) -> str:
    """Categorize CFO / PAT ratio quality."""
    if cfo_pat_ratio is None:
        return "N/A"
    if cfo_pat_ratio >= 1.0:
        return "High Quality Earnings"
    if cfo_pat_ratio < 0.5:
        return "Accrual Risk"
    return "Moderate Quality"


def get_capex_intensity_label(capex_intensity_pct: Optional[float]) -> str:
    """Categorize CapEx Intensity %."""
    if capex_intensity_pct is None:
        return "N/A"
    if capex_intensity_pct < 3.0:
        return "Asset-Light (<3%)"
    if capex_intensity_pct > 8.0:
        return "Capital Intensive (>8%)"
    return "Moderate CapEx (3-8%)"
