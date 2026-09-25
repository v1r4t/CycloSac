"""Hazard validation: bands sum 5%, depth range, timeline desc."""
from . import config


class StageError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code or config.EXIT_STAGE_INVARIANT


def validate_hazard(n: dict) -> dict:
    area = n.get("inundation_area_km2", 0)
    bands = n.get("depth_bands", [])
    if area and abs(sum(bands) - area) / area > 0.05:
        raise StageError(f"bands sum {sum(bands)} vs area {area}")
    if n.get("max_depth_m", 0) > 15:
        raise StageError(f"depth {n['max_depth_m']}m out of range")
    tl = sorted(n.get("timeline", []), key=lambda e: e["hours_before_landfall"], reverse=True)
    return {**n, "timeline": tl}
