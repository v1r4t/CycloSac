"""Deterministic Puri-scale demo inputs (seeded). Matches demo script beats."""
import json
import random
from pathlib import Path

SEED = 20260925


def build(d: Path) -> Path:
    rng = random.Random(SEED)
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    (d / "glossary").mkdir(exist_ok=True)
    w = lambda p, o: Path(p).write_text(json.dumps(o, indent=1))

    # Surge footprint: coastal strip (west part), depth 2.5m
    surge_poly = [[[85.45, 19.75], [85.58, 19.75], [85.58, 19.86], [85.45, 19.86], [85.45, 19.75]]]
    w(d / "surge.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"depth_m": 2.5},
         "geometry": {"type": "Polygon", "coordinates": surge_poly}}]})
    w(d / "rainfall.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"depth_m": 0.6},
         "geometry": {"type": "Polygon", "coordinates": [
             [[85.55, 19.80], [85.70, 19.80], [85.70, 19.90], [85.55, 19.90], [85.55, 19.80]]]}}]})
    w(d / "wind.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"wind_kmh": 165},
         "geometry": {"type": "Polygon", "coordinates": [
             [[85.40, 19.70], [85.75, 19.70], [85.75, 19.95], [85.40, 19.95], [85.40, 19.70]]]}}]})
    w(d / "aoi.geojson", {"type": "FeatureCollection", "features": []})
    w(d / "met.json", {"cyclone_name": "Michaung", "cyclone_category": 3,
                       "eta_landfall": "2026-09-27T06:00:00+05:30", "intensity_kmh": 165,
                       "forward_speed_kmh": 14, "rainfall_72h_mm": 320, "tide_phase": "high"})

    assets, audience = [], {}
    subs = []
    for i in range(17):  # coastal grid: first 11 inside surge strip
        lon = 85.46 + (i % 6) * 0.02 + rng.uniform(-0.003, 0.003)
        lat = 19.76 + (i // 6) * 0.03 + rng.uniform(-0.003, 0.003)
        aid = f"PURI-SUB-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Puri substation {i+1}",
                       "asset_type": "substation", "lat": round(lat, 5), "lon": round(lon, 5)})
        audience[aid] = "power_utility"
        subs.append(aid)
    hosps = []
    for i in range(4):
        aid = f"PURI-HOSP-{i+1:02d}"
        lat, lon = 19.78 + i * 0.02, 85.52 + i * 0.03
        assets.append({"asset_id": aid, "asset_name": f"Puri hospital {i+1}",
                       "asset_type": "hospital", "lat": lat, "lon": lon, "backup_power": i % 2 == 0})
        audience[aid] = "health_department"
        hosps.append(aid)
    for i in range(5):  # arterial roads
        aid = f"NH316-SEG-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"NH-316 segment {i+1}",
                       "asset_type": "arterial_road",
                       "lat": round(19.77 + i * 0.025, 5), "lon": round(85.50 + i * 0.02, 5)})
        audience[aid] = "roads_authority"
    for i in range(3):
        aid = f"PURI-WTR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Water plant {i+1}",
                       "asset_type": "water_plant", "lat": 19.79 + i * 0.02, "lon": 85.54 + i * 0.02})
        audience[aid] = "municipal_commissioner"
    for i in range(4):
        aid = f"PURI-TWR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Transmission tower {i+1}",
                       "asset_type": "transmission_tower", "lat": 19.76 + i * 0.03, "lon": 85.47 + i * 0.03})
        audience[aid] = "power_utility"
    for i in range(2):
        aid = f"PURI-SHEL-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Cyclone shelter {i+1}",
                       "asset_type": "cyclone_shelter", "lat": 19.82 + i * 0.04, "lon": 85.60 + i * 0.03})
        audience[aid] = "ndrf_commander"
    for aid in subs[:5]:
        audience[aid] = "power_utility"
    audience["PURI-SUB-01"] = "power_utility"

    deps = [{"from_asset": h, "to_asset": subs[i % len(subs)], "dependency_type": "power"}
            for i, h in enumerate(hosps)]
    deps += [{"from_asset": "PURI-SHEL-01", "to_asset": "NH316-SEG-01", "dependency_type": "access"},
             {"from_asset": "PURI-SHEL-02", "to_asset": "NH316-SEG-03", "dependency_type": "access"}]
    w(d / "assets.json", assets)
    w(d / "dependencies.json", deps)
    w(d / "population.json", [
        {"ward_code": "W1", "ward_name": "Sea Beach", "population": 12000, "vulnerability_index": 0.8},
        {"ward_code": "W2", "ward_name": "Town", "population": 25000, "vulnerability_index": 0.5},
        {"ward_code": "W3", "ward_name": "Port", "population": 8000, "vulnerability_index": 0.7},
        {"ward_code": "W4", "ward_name": "Rural", "population": 15000, "vulnerability_index": 0.4}])
    w(d / "audience.json", audience)
    w(d / "regional.json", {"forecast_id": "FC-2026-PURI-001", "district_name": "Puri",
                            "district_population": 1700000, "primary_language": "or",
                            "bbox": [85.40, 19.70, 85.75, 19.95]})
    w(d / "insurance.json", [
        {"asset_id": f"PURI-SUB-{i:02d}", "sum_insured_inr": 5000000, "insurer_id": "INS-1"}
        for i in (1, 3, 5, 7, 9)])
    w(d / "glossary" / "or.json", {"substation": "upakendra", "hospital": "chikitsalaya"})
    return d


if __name__ == "__main__":
    import sys
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "sample_inputs_demo"))
    print("demo inputs written")
