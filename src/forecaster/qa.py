"""QA: deterministic checks; score-reasoning mismatch = WARNING only."""
from . import config

BANNED = ["might", "could", "perhaps", "possibly", "maybe"]


def check_register(register, known_ids) -> list:
    flags = []
    for r in register or []:
        if r.get("asset_id") not in known_ids:
            flags.append({"severity": "BLOCKER", "check": "hallucination", "field": "asset_id",
                          "issue": f"unknown {r.get('asset_id')}", "suggested_fix": "drop or map to register"})
        if r.get("in_hazard") is False and r.get("vulnerability_score", 0) > 50:
            flags.append({"severity": "BLOCKER", "check": "contradiction", "field": "vulnerability_score",
                          "issue": f"{r.get('asset_id')} not in hazard but score {r.get('vulnerability_score')}",
                          "suggested_fix": "rescore or recheck exposure"})
        if r.get("hazard_depth_m", 0) > 10:
            flags.append({"severity": "BLOCKER", "check": "implausible", "field": "hazard_depth_m",
                          "issue": f"depth {r.get('hazard_depth_m')}", "suggested_fix": "verify footprint units"})
        bd = r.get("score_breakdown")
        if bd and abs(sum(bd.values()) - r.get("vulnerability_score", 0)) > 5:
            flags.append({"severity": "WARNING", "check": "breakdown-sum", "field": "score_breakdown",
                          "issue": "breakdown != score", "suggested_fix": "renormalize"})
    return flags


def check_advisories(advisories) -> list:
    flags = []
    for a in advisories or []:
        if any(w in a.get("message", "").lower().split() for w in BANNED):
            flags.append({"severity": "BLOCKER", "check": "hedging", "field": "message",
                          "issue": "banned hedging word", "suggested_fix": "rerun filter"})
    return flags


def summarize(flags) -> dict:
    blockers = sum(1 for f in flags if f.get("severity") == "BLOCKER")
    warns = sum(1 for f in flags if f.get("severity") == "WARNING")
    status = "block" if blockers else ("pass_with_warnings" if warns else "pass")
    return {"overall_status": status, "blocker_count": blockers, "flags": flags}


def check_parametric(parametric: dict) -> list:
    flags = []
    for e in (parametric or {}).get("payout_events", []):
        pct = e.get("payout_pct", 0)
        if not 0 <= pct <= 1:
            flags.append({"severity": "BLOCKER", "check": "parametric-range", "field": "payout_pct",
                          "issue": f"payout range violation: {pct}", "suggested_fix": "clamp to [0,1]"})
        if not e.get("trigger_condition"):
            flags.append({"severity": "WARNING", "check": "parametric-trigger", "field": "trigger_condition",
                          "issue": f"missing trigger for {e.get('asset_id')}", "suggested_fix": "record condition"})
    return flags


def check_counterfactual(counterfactual: list) -> list:
    pops = [r["exposed_pop"] for r in counterfactual or [] if "exposed_pop" in r]
    if pops != sorted(pops, reverse=True):
        return [{"severity": "WARNING", "check": "counterfactual-monotonicity",
                 "field": "exposed_pop", "issue": "COUNTERFACTUAL_NONMONOTONIC: exposed grows with lead time",
                 "suggested_fix": "recheck evacuation model"}]
    return []
