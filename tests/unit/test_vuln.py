"""Task 3b RED: vuln exposure + scoring + sort."""
from pyproj import Transformer
from forecaster import vuln


def _poly_lonlat():
    # ~200x200m square centered near 85.5,19.8
    return [[85.499, 19.799], [85.501, 19.799], [85.501, 19.801], [85.499, 19.801]]


def _shift_m(lon, lat, dx_m):
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:32645", always_xy=True)
    back = Transformer.from_crs("EPSG:32645", "EPSG:4326", always_xy=True)
    x, y = fwd.transform(lon, lat)
    lon2, lat2 = back.transform(x + dx_m, y)
    return lon2, lat2


def test_inside_outside():
    surge = [{"polygon": _poly_lonlat(), "depth_m": 2.0}]
    assets = [{"asset_id": "IN", "asset_name": "in", "asset_type": "substation",
               "lat": 19.8, "lon": 85.5},
              {"asset_id": "OUT", "asset_name": "out", "asset_type": "substation",
               "lat": 19.9, "lon": 85.6}]
    out = vuln.score_assets(assets, surge, [], [])
    by = {r["asset_id"]: r for r in out}
    assert by["IN"]["in_hazard"] is True and by["IN"]["hazard_depth_m"] == 2.0
    assert by["OUT"]["in_hazard"] is False
    assert out[0]["vulnerability_score"] >= out[1]["vulnerability_score"]


def test_near_boundary_ring():
    # east edge of square ~85.501; place points just outside edge center
    edge_lon, edge_lat = 85.501, 19.8
    lon_49, lat_49 = _shift_m(edge_lon, edge_lat, 49)
    lon_51, lat_51 = _shift_m(edge_lon, edge_lat, 51)
    surge = [{"polygon": _poly_lonlat(), "depth_m": 1.0}]
    assets = [{"asset_id": "N49", "asset_name": "n", "asset_type": "arterial_road",
               "lat": lat_49, "lon": lon_49},
              {"asset_id": "N51", "asset_name": "n", "asset_type": "arterial_road",
               "lat": lat_51, "lon": lon_51}]
    out = vuln.score_assets(assets, surge, [], [])
    by = {r["asset_id"]: r for r in out}
    assert by["N49"]["near_boundary"] is True
    assert by["N51"]["near_boundary"] is False
