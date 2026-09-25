"""Task 2 RED: loader fail-fast (exit 2) + happy path."""
import json
import pytest
from forecaster.loader import load_inputs, LoaderError
from forecaster import config


def _write(path, obj):
    path.write_text(json.dumps(obj))


def _minimal_inputs(tmp_path):
    (tmp_path / "glossary").mkdir()
    _write(tmp_path / "aoi.geojson", {"type": "FeatureCollection", "features": []})
    _write(tmp_path / "surge.geojson", {"type": "FeatureCollection", "features": []})
    _write(tmp_path / "rainfall.geojson", {"type": "FeatureCollection", "features": []})
    _write(tmp_path / "wind.geojson", {"type": "FeatureCollection", "features": []})
    _write(tmp_path / "met.json", {"cyclone_name": "Michaung", "cyclone_category": 2,
            "eta_landfall": "2026-09-27T06:00:00+05:30", "intensity_kmh": 150,
            "forward_speed_kmh": 15, "rainfall_72h_mm": 300, "tide_phase": "high"})
    _write(tmp_path / "assets.json", [
        {"asset_id": "A1", "asset_name": "Sub 1", "asset_type": "substation", "lat": 19.8, "lon": 85.5},
        {"asset_id": "A2", "asset_name": "Road 1", "asset_type": "arterial_road", "lat": 19.81, "lon": 85.51},
        {"asset_id": "A3", "asset_name": "Hosp 1", "asset_type": "hospital", "lat": 19.82, "lon": 85.52}])
    _write(tmp_path / "population.json", [{"ward_code": "W1", "ward_name": "W1", "population": 10000, "vulnerability_index": 0.5}])
    _write(tmp_path / "dependencies.json", [])
    _write(tmp_path / "audience.json", {"A1": "power_utility"})
    _write(tmp_path / "regional.json", {"forecast_id": "FC-T", "district_name": "Puri",
            "district_population": 100000, "primary_language": "or", "bbox": [85.0, 19.5, 86.0, 20.0]})
    _write(tmp_path / "insurance.json", [])
    _write(tmp_path / "glossary" / "or.json", {"substation": "upakendra"})
    return tmp_path


def test_loader_accepts_minimal(tmp_path):
    d = _minimal_inputs(tmp_path)
    inp = load_inputs(str(d))
    assert len(inp.assets) == 3
    assert inp.regional.forecast_id == "FC-T"


def test_loader_rejects_missing_asset_type(tmp_path):
    d = _minimal_inputs(tmp_path)
    bad = json.loads((d / "assets.json").read_text())
    del bad[0]["asset_type"]
    (d / "assets.json").write_text(json.dumps(bad))
    with pytest.raises(LoaderError) as e:
        load_inputs(str(d))
    assert e.value.code == config.EXIT_LOADER_FAIL
