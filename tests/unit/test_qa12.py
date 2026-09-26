"""QA-12 RED: parametric sanity + counterfactual monotonicity."""
from forecaster import qa


def test_parametric_payout_sanity():
    bad = {"payout_events": [{"asset_id": "S1", "payout_pct": 1.5, "payout_amount": 1}]}
    flags = qa.check_parametric(bad)
    assert any(f["severity"] == "BLOCKER" and "range" in f["issue"].lower() for f in flags)
    good = {"payout_events": [{"asset_id": "S1", "payout_pct": 0.4, "payout_amount": 4,
                               "trigger_condition": "wind>=150"}]}
    assert qa.check_parametric(good) == []


def test_counterfactual_monotonicity():
    cf = [{"horizon_h": 0, "exposed_pop": 1000}, {"horizon_h": 6, "exposed_pop": 1200}]
    flags = qa.check_counterfactual(cf)
    assert any("NONMONOTONIC" in f["issue"] for f in flags)
    ok = [{"horizon_h": 0, "exposed_pop": 1000}, {"horizon_h": 6, "exposed_pop": 800}]
    assert qa.check_counterfactual(ok) == []
