"""Counterfactual: static evac rate per horizon; exposed shrinks with lead time."""
from . import config

EVAC_PER_H = 0.02  # 2% of baseline evacuated per lead hour, capped


def build(baseline_exposed: int, baseline_cascades: int) -> list:
    rows = []
    for h in config.COUNTERFACTUAL_HORIZONS_H:
        frac = min(0.9, EVAC_PER_H * h)
        exposed = int(baseline_exposed * (1 - frac))
        rows.append({"horizon_h": h, "exposed_pop": exposed,
                     "reachable_shelters": max(1, baseline_cascades),
                     "cascade_chains_len": baseline_cascades,
                     "marginal_lives_saved": baseline_exposed - exposed})
    pops = [r["exposed_pop"] for r in rows]
    warnings = []
    if not all(a >= b for a, b in zip(pops, pops[1:])):
        warnings.append("COUNTERFACTUAL_NONMONOTONIC")
    rows.append({"warnings": warnings} if warnings else {})
    return [r for r in rows if "horizon_h" in r]
