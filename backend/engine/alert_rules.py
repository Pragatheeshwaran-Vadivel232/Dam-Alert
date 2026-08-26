from enum import Enum

# 1 CuSec flowing for 1 hour = 0.00028347 M.Cft
CUSEC_TO_MCFT_PER_HOUR = 0.00028347

class AlertLevel(str, Enum):
    NORMAL   = "NORMAL"
    CAUTION  = "CAUTION"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"
    LOW      = "LOW"
    RELEASE  = "RELEASE"

def calculate_fill_percent(storage_mcft: float,
                           full_cap_mcft: float) -> float:
    if not full_cap_mcft:
        return 0.0
    return round((storage_mcft / full_cap_mcft) * 100, 2)

def calculate_ttf_hours(storage_mcft: float,
                        full_cap_mcft: float,
                        inflow_cusecs: float,
                        outflow_cusecs: float):
    net_inflow = (inflow_cusecs or 0) - (outflow_cusecs or 0)
    if net_inflow <= 0:
        return None  # Dam not filling
    remaining = full_cap_mcft - storage_mcft
    ttf = remaining / (net_inflow * CUSEC_TO_MCFT_PER_HOUR)
    return round(ttf, 1)

def evaluate_alert_level(fill_pct: float,
                         ttf_hours,
                         inflow_cusecs: float,
                         prev_outflow: float,
                         curr_outflow: float) -> AlertLevel:

    # Water release: outflow switched from 0 to > 0
    if prev_outflow == 0 and curr_outflow > 0:
        return AlertLevel.RELEASE

    # Low water risk
    if fill_pct < 20 and (inflow_cusecs or 0) < 50:
        return AlertLevel.LOW

    # Critical
    if fill_pct > 95 or (ttf_hours is not None and ttf_hours < 6):
        return AlertLevel.CRITICAL

    # High
    if fill_pct > 85 or (ttf_hours is not None and ttf_hours < 24):
        return AlertLevel.HIGH

    # Caution
    if fill_pct > 70 or (ttf_hours is not None and ttf_hours < 48):
        return AlertLevel.CAUTION

    return AlertLevel.NORMAL
