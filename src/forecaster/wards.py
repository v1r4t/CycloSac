"""Ward assignment: point-in-polygon, round-robin fallback for outside points."""
from shapely.geometry import Point, shape


def assign(assets, wards_geojson, fallback_codes):
    polys = []
    for f in (wards_geojson or {}).get("features", []):
        try:
            polys.append((f["properties"]["ward_code"], shape(f["geometry"])))
        except Exception:
            continue
    out = {}
    for i, a in enumerate(assets):
        pt = Point(a.get("lon", 0), a.get("lat", 0))
        hit = next((code for code, poly in polys if poly.contains(pt) or poly.touches(pt)), None)
        out[a["asset_id"]] = hit or fallback_codes[i % len(fallback_codes)]
    return out
