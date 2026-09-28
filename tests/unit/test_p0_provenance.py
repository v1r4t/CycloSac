"""P0 acceptance: live/replay explicit, stale, fallback, as-of propagation."""
import json
from forecaster import gee_fetcher, weather_fetcher


def test_gee_live_success_carries_acquisition_and_freshness(tmp_path):
    def live(aoi, date):
        return {"cached": False, "source": "real", "aoi": aoi, "date": date,
                "date_acquired": date, "image_count": 2, "thumb_url": "http://t/x",
                "project": "p", "datasets": gee_fetcher.DATASETS,
                "requested_window": {"start": "a", "end": "b"},
                "fetched_at": "2026-09-25T00:00:00+00:00"}
    out = gee_fetcher.fetch_real_or_stub("AOI", "2026-09-25", str(tmp_path / "c"), live_fetch=live)
    assert out["source"] == "real"
    assert out["date_acquired"] == "2026-09-25"
    assert out["fetched_at"]
    prov = gee_fetcher.describe(out, "2026-09-25")
    assert prov["freshness"] == "live"
    assert prov["mode"] == "live_provider"


def test_gee_stale_cache_flagged(tmp_path):
    cache = tmp_path / "c"
    cache.mkdir()
    (cache / "tile.json").write_text(json.dumps({
        "cached": False, "source": "real", "aoi": "AOI", "date": "2026-09-20",
        "date_acquired": "2026-09-20", "fetched_at": "2026-09-20T00:00:00+00:00"}))
    out = gee_fetcher.fetch_real_or_stub("AOI", "2026-09-25", str(cache))
    assert out["cached"] is True
    prov = gee_fetcher.describe(out, "2026-09-25")
    assert prov["freshness"] == "stale"
    assert "stale" in prov["data_status"]


def test_gee_stub_is_explicit_fallback(tmp_path):
    out = gee_fetcher.fetch_real_or_stub(
        "AOI", "2026-09-25", str(tmp_path / "e"), live_fetch=lambda a, d: None)
    prov = gee_fetcher.describe(out, "2026-09-25")
    assert prov["freshness"] == "fallback"
    assert prov["mode"] == "fixture_fallback"


def test_weather_unavailable_provider_falls_back():
    values, prov = weather_fetcher.fetch(
        {"cyclone_name": "M", "cyclone_category": 3, "eta_landfall": "x",
         "intensity_kmh": 160, "forward_speed_kmh": 10,
         "rainfall_72h_mm": 100, "tide_phase": "high"},
        url="http://127.0.0.1:9/nope")
    assert prov["mode"] == "fixture_fallback"
    assert prov["freshness"] == "fallback"
    assert prov["error"]
