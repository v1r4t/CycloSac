"""P0-3 + P1: rainfall breakdown + dispatch fields."""
from forecaster import rainfall_pathways, dispatch


def test_rainfall_pathway_answers_who_what_why():
    reg = [
        {"asset_id": "RD-1", "asset_type": "arterial_road", "rainfall_depth_m": 0.4},
        {"asset_id": "H-1", "asset_type": "hospital", "rainfall_depth_m": 0.5},
        {"asset_id": "S-1", "asset_type": "cyclone_shelter", "rainfall_depth_m": 0.3},
        {"asset_id": "P-1", "asset_type": "substation", "rainfall_depth_m": 0.6},
    ]
    paths = rainfall_pathways.build(reg, 200)
    assert len(paths) == 4
    by_id = {p["asset_id"]: p for p in paths}
    assert by_id["RD-1"]["category"] == "flooded_road_access"
    assert by_id["H-1"]["category"] == "hospital_access_risk"
    assert by_id["S-1"]["category"] == "shelter_access_risk"
    assert by_id["P-1"]["category"] == "power_asset_risk"
    assert all(p["why_threshold"] and p["affected_population_note"] for p in paths)
    summary = rainfall_pathways.summarize(paths)
    assert summary["flooded_roads"] == ["RD-1"]
    assert "H-1" in summary["hospital_access_at_risk"]
    assert "P-1" in summary["power_assets_at_risk"]


def test_dispatch_has_recipient_retry_ack():
    recs = dispatch.build_records(
        [{"forecast_id": "F-1", "asset_refs": ["A-1"], "audience": "district_collector",
          "message": "Go", "channel": "sms"}], "dry-run")
    r = recs[0]
    assert r["recipient"]  # authority target, not just audience
    assert r["retry_count"] == 0
    assert r["ack"] in ("pending", "acknowledged")
    assert r["status"] == "prepared_for_review"
