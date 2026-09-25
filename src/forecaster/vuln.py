"""Vuln: UTM transform polys, buffer 50m ring, 35/25/20/10/10 scoring."""
from shapely.geometry import Point, Polygon
from shapely.ops import transform as shp_transform
from pyproj import Transformer
from . import config

_CRITICALITY = {"hospital": 20, "cyclone_shelter": 20, "substation": 16,
                "water_plant": 16, "transmission_tower": 12, "arterial_road": 12,
                "telecom_tower": 12}


def _to_utm(geom, fwd):
    return shp_transform(lambda x, y: fwd.transform(x, y), geom)


def _exposure(lat, lon, layers, crs):
    """layers: list of (utm_poly, utm_buffered, severity, kind). Returns (in_h, near, depth, wind, kind)."""
    fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = fwd.transform(lon, lat)
    pt = Point(x, y)
    best = None
    near = False
    for poly, buf, sev, kind in layers:
        inside = poly.contains(pt) or poly.touches(pt)
        in_buf = buf.contains(pt) or buf.touches(pt)
        if in_buf and not inside:
            near = True
        if inside and poly.boundary.distance(pt) < config.BUFFER_M:
            near = True
        if inside and (best is None or sev > best[0]):
            best = (sev, kind)
    if best is None:
        return False, near, 0.0, 0.0, "none"
    sev, kind = best
    if kind == "wind":
        return True, near, 0.0, sev, kind
    return True, near, sev, 0.0, kind


def _build_layers(surge, rainfall, wind, crs):
    fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    layers = []
    for s in surge or []:
        p = _to_utm(Polygon(s["polygon"]), fwd)
        layers.append((p, p.buffer(config.BUFFER_M), s.get("depth_m", 0), "surge"))
    for r in rainfall or []:
        p = _to_utm(Polygon(r["polygon"]), fwd)
        layers.append((p, p.buffer(config.BUFFER_M), r.get("depth_m", 0), "rainfall"))
    for w in wind or []:
        p = _to_utm(Polygon(w["polygon"]), fwd)
        layers.append((p, p.buffer(config.BUFFER_M), w.get("wind_kmh", 0), "wind"))
    return layers


def score_assets(assets, surge=None, rainfall=None, wind=None, crs=None):
    crs = crs or config.DEFAULT_CRS
    layers = _build_layers(surge, rainfall, wind, crs)
    out = []
    for a in assets:
        in_h, near, depth, wnd, kind = _exposure(a["lat"], a["lon"], layers, crs)
        atype = a["asset_type"]
        frag = config.FRAGILITY.get(atype, {})
        # hazard_exposure /35
        if kind == "wind":
            he = min(35.0, wnd / 200 * 35)
        else:
            he = min(35.0, depth / 3 * 35) if in_h else 0.0
        # fragility /25
        if kind == "wind" and "wind_kmh" in frag:
            af = 25.0 if wnd >= frag["wind_kmh"] else wnd / frag["wind_kmh"] * 25
        elif kind != "wind" and "inundation_m" in frag and frag["inundation_m"]:
            af = 25.0 if depth >= frag["inundation_m"] else depth / frag["inundation_m"] * 25
        else:
            af = 12.0 if in_h else 2.0
        crit = float(_CRITICALITY.get(atype, 10))
        acc = 8.0 if in_h else 3.0
        red = 3.0 if a.get("backup_power") else 8.0
        score = round(max(0, min(100, he + af + crit + acc + red)), 1)
        if kind == "wind":
            fm = f"wind {wnd}kmh vs rated {frag.get('wind_kmh', '?')}kmh"
        elif in_h:
            fm = f"inundation {depth}m vs threshold {frag.get('inundation_m', '?')}m"
        else:
            fm = "no direct inundation; access/cascade risk"
        out.append({"asset_id": a["asset_id"], "asset_name": a.get("asset_name", a["asset_id"]),
                    "asset_type": atype, "in_hazard": in_h,
                    "hazard_depth_m": depth if kind != "wind" else 0.0,
                    "hazard_wind_kmh": wnd, "hazard_type": kind, "near_boundary": near,
                    "vulnerability_score": score,
                    "reasoning": f"{kind} sev; frag {af:.0f}/25, exposure {he:.0f}/35"[:200],
                    "confidence": {"level": "high" if in_h or not near else "medium",
                                   "reason": "direct exposure" if in_h else "outside footprint"},
                    "estimated_failure_mode": fm, "population_affected": 0,
                    "data_gaps": [] if a.get("asset_type") else ["asset_type"],
                    "score_breakdown": {"hazard_exposure": round(he, 1), "asset_fragility": round(af, 1),
                                        "criticality": crit, "accessibility": acc, "redundancy": red}})
    out.sort(key=lambda r: r["vulnerability_score"], reverse=True)
    return out
