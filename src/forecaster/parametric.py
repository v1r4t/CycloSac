"""Parametric trigger: PAYOUT_TABLE lookup, orphan skip, range guard."""
from . import config


class ParametricError(Exception):
    def __init__(self, message, code_text="PARAMETRIC_RANGE_VIOLATION"):
        super().__init__(message)
        self.code = config.EXIT_STAGE_INVARIANT
        self.code_text = code_text


def check_pct(pct: float) -> float:
    if not 0 <= pct <= 1:
        raise ParametricError(f"payout_pct {pct} out of [0,1]")
    return pct


def payout_pct(max_wind_kmh: float, max_surge_m: float) -> float:
    best = 0.0
    for (w, s), pct in config.PAYOUT_TABLE.items():
        if max_wind_kmh >= w and max_surge_m >= s and pct > best:
            best = pct
    return check_pct(best)


def build_payouts(register, hazard_max: dict, insurance: list) -> dict:
    events, warnings = [], []
    reg_ids = {r["asset_id"] for r in register}
    for ins in insurance or []:
        aid = ins.get("asset_id")
        if aid not in reg_ids:
            warnings.append(f"PARAMETRIC_ORPHAN: {aid}")
            continue
        pct = payout_pct(hazard_max.get("wind_kmh", 0), hazard_max.get("surge_m", 0))
        amount = round(ins.get("sum_insured_inr", 0) * pct, 2)
        events.append({"asset_id": aid, "trigger_condition": f"wind>={hazard_max.get('wind_kmh')} surge>={hazard_max.get('surge_m')}",
                       "payout_pct": pct, "payout_amount": amount,
                       "insurer_id": ins.get("insurer_id", "INS-1"), "confidence": "high"})
    return {"payout_events": events, "warnings": warnings}
