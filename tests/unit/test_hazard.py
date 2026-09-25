"""Task 3 RED: hazard bands sum 5%, depth range, timeline sort."""
import pytest
from forecaster.hazard import validate_hazard, StageError
from forecaster import config


def _narrative(bands=(60.0, 40.0), area=100.0, max_depth=3.0, timeline=None):
    return {"inundation_area_km2": area, "depth_bands": list(bands),
            "max_depth_m": max_depth,
            "timeline": timeline or [{"hours_before_landfall": 48, "event": "a"},
                                     {"hours_before_landfall": 24, "event": "b"}]}


def test_bands_sum_ok():
    validate_hazard(_narrative())


def test_bands_off_6pct_aborts():
    with pytest.raises(StageError) as e:
        validate_hazard(_narrative(bands=(60.0, 34.0), area=100.0))
    assert e.value.code == config.EXIT_STAGE_INVARIANT


def test_depth_over_range_aborts():
    with pytest.raises(StageError):
        validate_hazard(_narrative(max_depth=16.0))


def test_timeline_sorted_desc():
    out = validate_hazard(_narrative(timeline=[
        {"hours_before_landfall": 24, "event": "b"},
        {"hours_before_landfall": 48, "event": "a"}]))
    assert out["timeline"][0]["hours_before_landfall"] == 48
