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

    # Surge footprint shifted onto the coastal landmass (verified against
    # JRC GSW1_4 surface-water: all asset cells below are land, occ < 20).
    # Water coverage inside the polygon is honest — surge comes from the sea.
    surge_poly = [[[85.55, 19.79], [85.68, 19.79], [85.68, 19.90], [85.55, 19.90], [85.55, 19.79]]]
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
    # Explicit land-verified cells (JRC GSW1_4 occurrence < 20, probed
    # 2026-09-27 on a 0.02 deg lattice). Jitter stays within cells.
    SUBS = [(85.57, 19.81), (85.59, 19.81), (85.61, 19.81), (85.575, 19.815),
            (85.57, 19.83), (85.59, 19.83), (85.61, 19.83),
            (85.59, 19.85), (85.61, 19.85),
            (85.43, 19.87), (85.45, 19.87), (85.47, 19.87),
            (85.57, 19.87), (85.59, 19.87), (85.61, 19.87),
            (85.43, 19.89), (85.452, 19.888)]
    for i, (lon, lat) in enumerate(SUBS):
        aid = f"PURI-SUB-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Puri substation {i+1}",
                       "asset_type": "substation", "lat": round(lat, 5), "lon": round(lon, 5)})
        audience[aid] = "power_utility"
        subs.append(aid)
    hosps = []
    for i, (lon, lat) in enumerate([(85.65, 19.87), (85.59, 19.85), (85.65, 19.85), (85.49, 19.89)]):
        aid = f"PURI-HOSP-{i+1:02d}"
        lat, lon = round(lat, 5), round(lon, 5)
        assets.append({"asset_id": aid, "asset_name": f"Puri hospital {i+1}",
                       "asset_type": "hospital", "lat": lat, "lon": lon, "backup_power": i % 2 == 0})
        audience[aid] = "health_department"
        hosps.append(aid)
    for i, (lon, lat) in enumerate([(85.43, 19.85), (85.45, 19.85), (85.51, 19.89), (85.53, 19.89), (85.63, 19.87)]):
        aid = f"NH316-SEG-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"NH-316 segment {i+1}",
                       "asset_type": "arterial_road",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "roads_authority"
    for i, (lon, lat) in enumerate([(85.65, 19.85), (85.67, 19.85), (85.67, 19.89)]):
        aid = f"PURI-WTR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Water plant {i+1}",
                       "asset_type": "water_plant",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "municipal_commissioner"
    for i, (lon, lat) in enumerate([(85.41, 19.85), (85.41, 19.87), (85.49, 19.87), (85.65, 19.89)]):
        aid = f"PURI-TWR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Transmission tower {i+1}",
                       "asset_type": "transmission_tower",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "power_utility"
    for i, (lon, lat) in enumerate([(85.69, 19.89), (85.71, 19.89)]):
        aid = f"PURI-SHEL-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Cyclone shelter {i+1}",
                       "asset_type": "cyclone_shelter",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
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
    # Ward quadrants of the AOI bbox (mid 85.575 / 19.825); real geometries
    # so assets map to wards spatially instead of round-robin.
    mx, my = 85.575, 19.825
    quads = {"W1": [[85.40, 19.70], [mx, 19.70], [mx, my], [85.40, my]],
             "W2": [[mx, 19.70], [85.75, 19.70], [85.75, my], [mx, my]],
             "W3": [[85.40, my], [mx, my], [mx, 19.95], [85.40, 19.95]],
             "W4": [[mx, my], [85.75, my], [85.75, 19.95], [mx, 19.95]]}
    w(d / "wards.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ward_code": k},
         "geometry": {"type": "Polygon", "coordinates": [v + [v[0]]]}}
        for k, v in quads.items()]})
    w(d / "glossary" / "or.json", {"substation": "upakendra", "hospital": "chikitsalaya"})
    (d / ".geecache").mkdir(exist_ok=True)
    w(d / ".geecache" / "tile.json", {"cached": False, "source": "stub",
                                      "aoi": "demo", "date": "2026-09-25",
                                      "note": "demo stub; live tile fetched separately"})
    return d


if __name__ == "__main__":
    import sys
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "sample_inputs_demo"))
    print("demo inputs written")
