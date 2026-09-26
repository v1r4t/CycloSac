"""Helper: build minimal valid inputs dir for E2E."""
import json
from pathlib import Path


def make_inputs(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "glossary").mkdir(exist_ok=True)
    w = lambda p, o: Path(p).write_text(json.dumps(o))
    w(d / "aoi.geojson", {"type": "FeatureCollection", "features": []})
    w(d / "surge.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"depth_m": 2.0},
         "geometry": {"type": "Polygon", "coordinates": [
             [[85.499, 19.799], [85.501, 19.799], [85.501, 19.801], [85.499, 19.801], [85.499, 19.799]]]}}]})
    w(d / "rainfall.geojson", {"type": "FeatureCollection", "features": []})
    w(d / "wind.geojson", {"type": "FeatureCollection", "features": []})
    w(d / "met.json", {"cyclone_name": "Michaung", "cyclone_category": 2,
                       "eta_landfall": "2026-09-27T06:00:00+05:30", "intensity_kmh": 160,
                       "forward_speed_kmh": 15, "rainfall_72h_mm": 300, "tide_phase": "high"})
    w(d / "assets.json", [
        {"asset_id": "S1", "asset_name": "Sub Puri-04", "asset_type": "substation", "lat": 19.8, "lon": 85.5},
        {"asset_id": "R1", "asset_name": "NH-316", "asset_type": "arterial_road", "lat": 19.82, "lon": 85.52},
        {"asset_id": "H1", "asset_name": "CHC Puri", "asset_type": "hospital", "lat": 19.85, "lon": 85.55}])
    w(d / "population.json", [
        {"ward_code": "W1", "ward_name": "Sea Beach", "population": 10000, "vulnerability_index": 0.7},
        {"ward_code": "W2", "ward_name": "Town", "population": 20000, "vulnerability_index": 0.4}])
    w(d / "dependencies.json", [
        {"from_asset": "S1", "to_asset": "H1", "dependency_type": "power"}])
    w(d / "audience.json", {"S1": "power_utility", "R1": "roads_authority", "H1": "health_department"})
    w(d / "regional.json", {"forecast_id": "FC-2026-E2E", "district_name": "Puri",
                            "district_population": 1700000, "primary_language": "or",
                            "bbox": [85.0, 19.5, 86.0, 20.0]})
    w(d / "insurance.json", [
        {"asset_id": "S1", "sum_insured_inr": 5000000, "insurer_id": "INS-1"}])
    w(d / "glossary" / "or.json", {"substation": "upakendra"})
    (d / ".geecache").mkdir(exist_ok=True)
    w(d / ".geecache" / "tile.json", {"cached": False, "source": "stub",
                                      "aoi": "test", "date": "2026-09-25",
                                      "note": "test stub; live path covered manually"})
    return d
