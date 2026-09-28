from forecaster import dispatch, rainfall_pathways, weather_fetcher


FIXTURE = {
    "cyclone_name": "Demo", "cyclone_category": 3,
    "eta_landfall": "2026-09-27T00:00:00+05:30", "intensity_kmh": 160,
    "forward_speed_kmh": 15, "rainfall_72h_mm": 180, "tide_phase": "high",
}


def test_weather_fixture_is_explicitly_a_replay():
    values, provenance = weather_fetcher.fetch(FIXTURE)
    assert values == FIXTURE
    assert provenance["mode"] == "fixture_replay"
    assert provenance["freshness"] == "replay"


def test_weather_normalizes_provider_aliases():
    normalized = weather_fetcher.normalize({"wind_kmh": 175, "rainfall_mm": 220}, FIXTURE)
    assert normalized["intensity_kmh"] == 175
    assert normalized["rainfall_72h_mm"] == 220
    assert normalized["cyclone_name"] == "Demo"


def test_dispatch_never_sends_and_keeps_approval_state():
    records = dispatch.build_records([{"forecast_id": "F-1", "asset_refs": ["A-1"],
                                       "audience": "roads_authority", "message": "Act now"}], "approved")
    assert records[0]["status"] == "approved_for_delivery"
    assert records[0]["delivery_performed"] is False


def test_rainfall_pathway_requires_footprint_and_threshold():
    register = [{"asset_id": "R1", "asset_type": "arterial_road", "rainfall_depth_m": 0.4},
                {"asset_id": "H1", "asset_type": "hospital", "rainfall_depth_m": 0.0}]
    paths = rainfall_pathways.build(register, 150)
    assert [p["asset_id"] for p in paths] == ["R1"]
    assert paths[0]["severity"] == "high"
