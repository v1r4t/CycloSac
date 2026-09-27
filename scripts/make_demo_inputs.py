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

    # Surge strip hugging the real shoreline (sea overlap honest).
    surge_poly = [[[85.78, 19.775], [85.94, 19.775], [85.95, 19.89], [85.79, 19.89], [85.78, 19.775]]]
    w(d / "surge.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"depth_m": 2.5},
         "geometry": {"type": "Polygon", "coordinates": surge_poly}}]})
    w(d / "rainfall.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"depth_m": 0.6},
         "geometry": {"type": "Polygon", "coordinates": [
             [[85.78, 19.80], [85.95, 19.80], [85.95, 19.92], [85.78, 19.92], [85.78, 19.80]]]}}]})
    w(d / "wind.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"wind_kmh": 165},
         "geometry": {"type": "Polygon", "coordinates": [
             [[85.75, 19.75], [85.98, 19.75], [85.98, 19.95], [85.75, 19.95], [85.75, 19.75]]]}}]})
    w(d / "aoi.geojson", {"type": "FeatureCollection", "features": []})
    w(d / "met.json", {"cyclone_name": "Michaung", "cyclone_category": 3,
                       "eta_landfall": "2026-09-27T06:00:00+05:30", "intensity_kmh": 165,
                       "forward_speed_kmh": 14, "rainfall_72h_mm": 320, "tide_phase": "high"})

    assets, audience = [], {}
    subs = []
    # Explicit land-verified cells (JRC GSW1_4 occurrence < 20, probed
    # 2026-09-27 on a 0.02 deg lattice). Jitter stays within cells.
    # Puri CITY ground (not the old Chilika-rural grid): every coordinate below
    # is SRTM-verified land (elev >= 3) via live GEE 2026-09-27. GSW occurrence
    # nulls over dense town are a mask quirk (temple max_extent == 0 = certain
    # land); combined rule WATER iff gsw_occ >= 50 or srtm < 3.
    SUBS = [(85.8312, 19.8135), (85.825, 19.818), (85.82, 19.81),
            (85.836, 19.812), (85.841, 19.8079), (85.835, 19.804),
            (85.85, 19.82), (85.858, 19.83), (85.82, 19.818),
            (85.845, 19.815), (85.855, 19.825), (85.80, 19.815),
            (85.87, 19.825), (85.845, 19.83),
            (85.45, 19.87), (85.47, 19.89), (85.43, 19.89)]
    for i, (lon, lat) in enumerate(SUBS):
        aid = f"PURI-SUB-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Puri substation {i+1}",
                       "asset_type": "substation", "lat": round(lat, 5), "lon": round(lon, 5)})
        audience[aid] = "power_utility"
        subs.append(aid)
    hosps = []
    for i, (lon, lat) in enumerate([(85.86, 19.815), (85.85, 19.83), (85.845, 19.855), (85.836, 19.809)]):
        aid = f"PURI-HOSP-{i+1:02d}"
        lat, lon = round(lat, 5), round(lon, 5)
        assets.append({"asset_id": aid, "asset_name": f"Puri hospital {i+1}",
                       "asset_type": "hospital", "lat": lat, "lon": lon, "backup_power": i % 2 == 0})
        audience[aid] = "health_department"
        hosps.append(aid)
    for i, (lon, lat) in enumerate([(85.835, 19.804), (85.85, 19.82), (85.858, 19.83), (85.86, 19.86), (85.85, 19.87)]):
        aid = f"NH316-SEG-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"NH-316 segment {i+1}",
                       "asset_type": "arterial_road",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "roads_authority"
    for i, (lon, lat) in enumerate([(85.845, 19.855), (85.87, 19.86), (85.58, 19.83)]):
        aid = f"PURI-WTR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Water plant {i+1}",
                       "asset_type": "water_plant",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "municipal_commissioner"
    for i, (lon, lat) in enumerate([(85.80, 19.815), (85.89, 19.85), (85.60, 19.89), (85.87, 19.87)]):
        aid = f"PURI-TWR-{i+1:02d}"
        assets.append({"asset_id": aid, "asset_name": f"Transmission tower {i+1}",
                       "asset_type": "transmission_tower",
                       "lat": round(lat, 5),
                       "lon": round(lon, 5)})
        audience[aid] = "power_utility"
    for i, (lon, lat) in enumerate([(85.86, 19.86), (85.85, 19.87)]):
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
                            "bbox": [85.78, 19.78, 85.95, 19.92]})
    w(d / "insurance.json", [
        {"asset_id": f"PURI-SUB-{i:02d}", "sum_insured_inr": 5000000, "insurer_id": "INS-1"}
        for i in (1, 3, 5, 7, 9)])
    # Ward quadrants of the city AOI bbox (mid 85.865 / 19.85).
    mx, my = 85.865, 19.85
    quads = {"W1": [[85.78, 19.78], [mx, 19.78], [mx, my], [85.78, my]],
             "W2": [[mx, 19.78], [85.95, 19.78], [85.95, my], [mx, my]],
             "W3": [[85.78, my], [mx, my], [mx, 19.92], [85.78, 19.92]],
             "W4": [[mx, my], [85.95, my], [85.95, 19.92], [mx, 19.92]]}
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
