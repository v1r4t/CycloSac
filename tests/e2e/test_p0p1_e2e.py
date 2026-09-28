"""E2E: --as-of propagation, --weather-url fallback/live, GEE live cache write."""
import json


def test_cli_as_of_propagates_to_forecast_and_gee(tmp_path):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    assert CLI.main(["--inputs", str(inp), "--out", str(out),
                     "--as-of", "2026-09-25T06:00:00+05:30"]) == 0
    fc = json.loads(out.read_text())
    assert fc["as_of"] == "2026-09-25T06:00:00+05:30"
    assert fc["gee_tile"]["date"] == "2026-09-25"


def test_cli_bad_weather_url_falls_back_and_exits_0(tmp_path):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    assert CLI.main(["--inputs", str(inp), "--out", str(out),
                     "--weather-url", "http://127.0.0.1:9/nope"]) == 0
    prov = json.loads(out.read_text())["weather"]["provenance"]
    assert prov["mode"] == "fixture_fallback"
    assert prov["freshness"] == "fallback"


def test_cli_weather_url_live_file(tmp_path):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    live = tmp_path / "live.json"
    live.write_text(json.dumps({"wind_kmh": 175, "rainfall_mm": 220}))
    out = tmp_path / "forecast.json"
    assert CLI.main(["--inputs", str(inp), "--out", str(out),
                     "--weather-url", live.as_uri()]) == 0
    fc = json.loads(out.read_text())
    assert fc["weather"]["provenance"]["mode"] == "live_provider"
    assert fc["weather"]["values"]["intensity_kmh"] == 175


def test_gee_live_success_writes_cache(tmp_path):
    from forecaster import gee_fetcher
    live = {"cached": False, "source": "real", "aoi": "A", "date": "2026-09-25",
            "date_acquired": "2026-09-25", "image_count": 2,
            "fetched_at": "2026-09-25T00:00:00+00:00"}
    out = gee_fetcher.fetch_real_or_stub("A", "2026-09-25", str(tmp_path / "c"),
                                         live_fetch=lambda a, d: dict(live))
    assert out["source"] == "real"
    assert (tmp_path / "c" / "tile.json").exists()
    prov = gee_fetcher.describe(out, "2026-09-25")
    assert prov["freshness"] == "live"
