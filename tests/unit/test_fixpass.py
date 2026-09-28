"""Fix-pass RED: summarize service bucket, LLM verdict parse, disagreement label."""
from forecaster import rainfall_pathways, gemini_conflict


def test_summarize_keeps_service_disruption_bucket():
    paths = [
        {"asset_id": "W-1", "category": "service_disruption_risk"},
        {"asset_id": "R-1", "category": "flooded_road_access"},
    ]
    s = rainfall_pathways.summarize(paths)
    assert s["services_at_risk"] == ["W-1"]
    assert s["total_pathways"] == 2


def test_llm_verdict_requires_conflict_prefix():
    bands = {"sar_water_frac": 0.8, "model_surge_m": 0.3}
    out = gemini_conflict.detect_with_llm(
        "t", bands, [], complete=lambda p: "I see eyes yesterday, all calm. Conflict: no.")
    assert out == [] or all(c["generation_mode"] == "template_heuristic" for c in out)


def test_llm_no_with_heuristic_fired_stays_heuristic_with_disagreement():
    bands = {"sar_water_frac": 0.9, "model_surge_m": 0.2}
    out = gemini_conflict.detect_with_llm(
        "t", bands, [], complete=lambda p: "Conflict: no. SAR looks fine.")
    assert len(out) == 1
    assert out[0]["generation_mode"] == "template_heuristic"
    assert out[0].get("llm_disagreement") is True
