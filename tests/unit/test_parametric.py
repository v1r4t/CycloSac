"""Task 4b RED: parametric payout lookup + counterfactual monotonicity."""
import pytest
from forecaster import parametric, counterfactual


def test_payout_lookup():
    assert parametric.payout_pct(160, 1.6) == 0.40
    assert parametric.payout_pct(210, 3.1) == 1.00
    assert parametric.payout_pct(100, 0.5) == 0.0


def test_payout_monotonic():
    assert parametric.payout_pct(200, 3.0) >= parametric.payout_pct(150, 1.5)


def test_payout_range_violation():
    with pytest.raises(parametric.ParametricError) as e:
        parametric.check_pct(1.5)
    assert e.value.code_text == "PARAMETRIC_RANGE_VIOLATION"


def test_counterfactual_baseline_and_monotonic():
    m = counterfactual.build(baseline_exposed=10000, baseline_cascades=3)
    assert m[0]["horizon_h"] == 0 and m[0]["exposed_pop"] == 10000
    pops = [r["exposed_pop"] for r in m]
    assert all(b >= a for a, b in zip(pops, pops[1:])) is False  # exposed shrinks with lead time
    assert all(a >= b for a, b in zip(pops, pops[1:]))
