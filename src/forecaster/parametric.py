"""Parametric trigger: PAYOUT_TABLE lookup, orphan skip, range guard."""
from . import config

EVIDENCE_REQUIRED = [
    "validated hazard observation", "policy eligibility", "insurer approval"]


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
                       "insurer_id": ins.get("insurer_id", "INS-1"), "policy_id": ins.get("policy_id"),
                       "sum_insured_inr": ins.get("sum_insured_inr", 0), "confidence": "high",
                       "evidence": {"wind_kmh": hazard_max.get("wind_kmh", 0),
                                    "surge_m": hazard_max.get("surge_m", 0),
                                    "trigger_table": "configured parametric payout table"},
                       "settlement_status": "simulated_pending_insurer_review"})
    return {"payout_events": events, "warnings": warnings,
            "settlement_mode": "simulated", "evidence_required": list(EVIDENCE_REQUIRED)}


def review(event: dict, decision: str = "approved", reviewer: str = "insurer") -> dict:
    """Insurer-review transition. Ledger stays simulated; never a payment claim."""
    out = dict(event)
    if decision == "approved":
        out.update({"settlement_status": "simulated_approved_by_insurer",
                    "approved_by": reviewer})
    elif decision == "rejected":
        out.update({"settlement_status": "simulated_rejected_by_insurer",
                    "approved_by": reviewer})
    else:
        out.update({"settlement_status": "simulated_pending_insurer_review"})
    return out


def evidence_record(event: dict, hazard_max: dict, forecast_id: str) -> dict:
    """Downloadable trigger-and-evidence record for an insurer."""
    return {
        "forecast_id": forecast_id,
        "asset_id": event.get("asset_id"),
        "policy_id": event.get("policy_id"),
        "hazard_inputs": {"wind_kmh": hazard_max.get("wind_kmh"),
                          "surge_m": hazard_max.get("surge_m")},
        "trigger_logic": event.get("trigger_condition"),
        "trigger_table": (event.get("evidence") or {}).get("trigger_table"),
        "payout_pct": event.get("payout_pct"),
        "payout_amount": event.get("payout_amount"),
        "settlement_status": event.get("settlement_status"),
        "next_steps": list(EVIDENCE_REQUIRED),
    }
