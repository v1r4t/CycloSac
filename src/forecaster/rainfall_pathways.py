"""Translate rainfall exposure into explainable infrastructure pathways."""
from __future__ import annotations

from . import config


def _category(asset_type: str) -> str:
    return {
        "arterial_road": "flooded_road_access",
        "hospital": "hospital_access_risk",
        "cyclone_shelter": "shelter_access_risk",
        "substation": "power_asset_risk",
        "transmission_tower": "power_asset_risk",
        "telecom_tower": "power_asset_risk",
        "water_plant": "service_disruption_risk",
    }.get(asset_type, "service_disruption_risk")


def build(register: list[dict], rainfall_72h_mm: float) -> list[dict]:
    pathways = []
    for asset in register or []:
        atype = asset.get("asset_type", "unknown")
        aid = asset.get("asset_id", "unknown")
        threshold = config.RAINFALL_PATHWAY_THRESHOLDS_MM.get(atype, 150)
        footprint_depth = float(asset.get("rainfall_depth_m", 0) or 0)
        if rainfall_72h_mm < threshold or footprint_depth <= 0:
            continue
        role = ("access and evacuation route" if atype == "arterial_road"
                else "continuity of critical service")
        pathways.append({
            "asset_id": aid, "asset_type": atype,
            "rainfall_72h_mm": rainfall_72h_mm, "threshold_mm": threshold,
            "footprint_depth_m": footprint_depth,
            "category": _category(atype),
            "impact_pathway": f"Heavy rainfall can disrupt {role} at this asset.",
            "severity": "high" if rainfall_72h_mm >= threshold * 1.5 else "moderate",
            "recommended_action": "Inspect drainage/access route and pre-position an alternate service path.",
            "why_threshold": (f"72h rainfall {rainfall_72h_mm}mm crossed {atype} "
                              f"threshold {threshold}mm with footprint depth {footprint_depth}m."),
            "affected_population_note": ("Access loss isolates dependent wards; "
                                         "see cascade ward union for headcount."),
        })
    return pathways


def summarize(pathways: list[dict]) -> dict:
    """Answer: which roads, hospitals, shelters, power assets are threatened, and why."""
    return {
        "flooded_roads": [p["asset_id"] for p in pathways if p.get("category") == "flooded_road_access"],
        "hospital_access_at_risk": [p["asset_id"] for p in pathways if p.get("category") == "hospital_access_risk"],
        "shelter_access_at_risk": [p["asset_id"] for p in pathways if p.get("category") == "shelter_access_risk"],
        "power_assets_at_risk": [p["asset_id"] for p in pathways if p.get("category") == "power_asset_risk"],
        "services_at_risk": [p["asset_id"] for p in pathways if p.get("category") == "service_disruption_risk"],
        "total_pathways": len(pathways),
    }
