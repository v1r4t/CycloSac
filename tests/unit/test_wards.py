"""RED: assets map to wards by point-in-polygon, fallback round-robin."""
from forecaster import wards


def _quads():
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ward_code": "W1"},
         "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}},
        {"type": "Feature", "properties": {"ward_code": "W2"},
         "geometry": {"type": "Polygon", "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]]}}]}


def test_point_in_ward():
    assets = [{"asset_id": "A", "lat": 0.5, "lon": 0.5}, {"asset_id": "B", "lat": 0.5, "lon": 1.5}]
    assert wards.assign(assets, _quads(), ["W1", "W2"]) == {"A": "W1", "B": "W2"}


def test_outside_falls_back():
    assets = [{"asset_id": "Z", "lat": 50.0, "lon": 50.0}]
    assert wards.assign(assets, _quads(), ["W1", "W2"])["Z"] in {"W1", "W2"}
