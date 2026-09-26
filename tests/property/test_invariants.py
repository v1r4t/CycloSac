"""Property invariants (Sec 4): stdlib random only, seeded for determinism."""
import random

import pytest

from forecaster import cascade, qa
from forecaster.hazard import StageError, validate_hazard

N = 200
rng = random.Random(20260925)


def _narrative(bands, area):
    return {"inundation_area_km2": area, "depth_bands": list(bands),
            "max_depth_m": 3.0,
            "timeline": [{"hours_before_landfall": 48, "event": "a"}]}


def test_bands_sum_within_5pct_passes():
    for _ in range(N):
        area = rng.uniform(10, 1000)
        # random 2-band split perturbed within +-4.9%
        b1 = rng.uniform(0, area)
        target = area * rng.uniform(0.951, 1.049)
        bands = [b1, max(0.0, target - b1)]
        validate_hazard(_narrative(bands, area))


def test_bands_sum_beyond_5pct_aborts():
    for _ in range(N):
        area = rng.uniform(10, 1000)
        sign = rng.choice([-1, 1])
        off = rng.uniform(0.06, 0.20)  # 6-20% off
        bands = [area * (1 + sign * off)]
        with pytest.raises(StageError):
            validate_hazard(_narrative(bands, area))


def test_bands_sum_exact_5pct_boundary_passes():
    validate_hazard(_narrative([105.0], 100.0))  # exactly 5% passes (> 0.05 aborts)
    with pytest.raises(StageError):
        validate_hazard(_narrative([105.01], 100.0))


def test_breakdown_sum_within_5_no_warning():
    for _ in range(N):
        score = round(rng.uniform(10, 100), 1)
        parts = [rng.random() for _ in range(5)]
        s = sum(parts)
        target = score + rng.uniform(-4.9, 4.9)
        scaled = [round(p / s * target, 1) for p in parts]
        reg = [{"asset_id": "A1", "in_hazard": True, "vulnerability_score": score,
                "hazard_depth_m": 1.0,
                "score_breakdown": {"hazard_exposure": scaled[0], "asset_fragility": scaled[1],
                                    "criticality": scaled[2], "accessibility": scaled[3],
                                    "redundancy": scaled[4]}}]
        # renormalize rounding drift so diff stays <= 5
        drift = abs(sum(scaled) - score)
        assert drift <= 5.5  # sanity on the generator itself
        flags = [f for f in qa.check_register(reg, {"A1"}) if f["check"] == "breakdown-sum"]
        if drift <= 5:
            assert flags == []
        else:
            assert len(flags) == 1 and flags[0]["severity"] == "WARNING"


def test_breakdown_sum_beyond_5_warns():
    reg = [{"asset_id": "A1", "in_hazard": True, "vulnerability_score": 80.0,
            "hazard_depth_m": 1.0,
            "score_breakdown": {"hazard_exposure": 10.0, "asset_fragility": 10.0,
                                "criticality": 10.0, "accessibility": 10.0, "redundancy": 10.0}}]
    flags = [f for f in qa.check_register(reg, {"A1"}) if f["check"] == "breakdown-sum"]
    assert len(flags) == 1 and flags[0]["severity"] == "WARNING"


def test_union_le_sum():
    for _ in range(N):
        n = rng.randint(2, 6)
        ids = [f"A{i}" for i in range(n)]
        reg = [{"asset_id": i, "vulnerability_score": 80 if j == 0 else 10}
               for j, i in enumerate(ids)]
        deps = [{"from_asset": ids[k], "to_asset": ids[k + 1], "dependency_type": "power"}
                for k in range(rng.randint(0, n - 1))]
        wards = ["W1", "W2", "W3"]
        award = {i: rng.choice(wards) for i in ids}
        wpop = {"W1": 1000, "W2": 500, "W3": 250}
        out = cascade.build(reg, deps, asset_ward=award, ward_pop=wpop)
        per_chain = sum(c["population_affected"] for c in out["cascade_chains"])
        assert out["cumulative_population_affected"] <= per_chain
        assert out["cumulative_population_affected"] <= sum(wpop.values())


def test_blocker_count_exact():
    for _ in range(N):
        flags = [{"severity": rng.choice(["BLOCKER", "WARNING"])} for _ in range(rng.randint(0, 10))]
        s = qa.summarize(flags)
        assert s["blocker_count"] == sum(1 for f in flags if f["severity"] == "BLOCKER")
        assert (s["overall_status"] == "block") == (s["blocker_count"] > 0)
