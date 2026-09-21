from typing import Any, Dict, Optional, Tuple


def calculate_cagr(base_val: Optional[float], end_val: Optional[float], n: int) -> Tuple[Optional[float], str, str]:
    """Calculate Compound Annual Growth Rate with edge case handling.
    
    Returns (cagr_val_pct, flag, display_text)
    """
    if base_val is None or end_val is None or n <= 0:
        return None, "INSUFFICIENT", "N/A — < 3yr"

    try:
        b = float(base_val)
        e = float(end_val)
    except (ValueError, TypeError):
        return None, "INSUFFICIENT", "N/A — < 3yr"

    if b == 0:
        return None, "ZERO_BASE", "N/A — base=0"
    
    if b > 0 and e > 0:
        val = ((e / b) ** (1.0 / n) - 1.0) * 100.0
        return round(val, 2), "NORMAL", f"{val:.1f}%"
    
    if b > 0 and e < 0:
        return None, "DECLINE_TO_LOSS", "N/A — turned loss"
    
    if b < 0 and e > 0:
        return None, "TURNAROUND", "Turnaround ↑"
    
    if b < 0 and e < 0:
        return None, "BOTH_NEGATIVE", "N/A — both loss"

    return None, "INSUFFICIENT", "N/A"
