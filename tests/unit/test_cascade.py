"""Task 4 RED: cascade BFS depth-3, ward-union pop, cycle/unknown handling."""
import pytest
from forecaster import cascade


def _reg(*scores):
    return [{"asset_id": f"A{i+1}", "vulnerability_score": s} for i, s in enumerate(scores)]


WARD = {"A1": "W1", "A2": "W1", "A3": "W2"}
WPOP = {"W1": 1000, "W2": 500}


def test_chain_and_union():
    reg = _reg(80, 50, 50)
    deps = [{"from_asset": "A1", "to_asset": "A2", "dependency_type": "power"},
            {"from_asset": "A2", "to_asset": "A3", "dependency_type": "power"}]
    out = cascade.build(reg, deps, asset_ward=WARD, ward_pop=WPOP)
    assert len(out["cascade_chains"]) == 1
    assert out["cascade_chains"][0]["max_depth"] == 2
    assert out["cascade_chains"][0]["chain"][0]["dependency_type"] == "power"
    assert out["cascade_chains"][0]["chain"][0]["hop"] == 1
    assert out["cumulative_population_affected"] == 1500  # W1+W2 union, not 2500 sum


def test_no_trigger_no_chain():
    out = cascade.build(_reg(60, 50), [], asset_ward=WARD, ward_pop=WPOP)
    assert out["cascade_chains"] == [] and out["cumulative_population_affected"] == 0


def test_depth_truncated_at_3():
    reg = _reg(90, 10, 10, 10, 10)
    deps = [{"from_asset": f"A{i}", "to_asset": f"A{i+1}", "dependency_type": "power"} for i in range(1, 5)]
    out = cascade.build(reg, deps)
    assert out["cascade_chains"][0]["max_depth"] == 3


def test_cycle_warns_not_hangs():
    reg = _reg(85, 10)
    deps = [{"from_asset": "A1", "to_asset": "A2", "dependency_type": "power"},
            {"from_asset": "A2", "to_asset": "A1", "dependency_type": "power"}]
    out = cascade.build(reg, deps)
    assert any("cycle" in c.lower() for c in out["critical_paths"])


def test_unknown_trigger_aborts():
    with pytest.raises(cascade.CascadeError) as e:
        cascade.build(_reg(80), [{"from_asset": "ZZ", "to_asset": "A1", "dependency_type": "power"}], {})
    assert e.value.code_text == "CASCADE_TRIGGER_UNKNOWN"
