"""Gemini Path2 multimodal conflict detector (stub, never blocks)."""

from __future__ import annotations

from typing import Any


def _check(tile_ref: str, bands: dict, assets: list) -> list[dict]:
    """Pure heuristic: SAR-water vs low-model-surge toy rule. Raises on bad input."""
    if not isinstance(bands, dict):
        raise TypeError("bands must be dict")
    sar = bands.get("sar_water", bands.get("sar_water_frac", 0))
    surge = bands.get("model_surge_m", bands.get("surge_m", 0))
    if not isinstance(sar, (int, float)) or not isinstance(surge, (int, float)):
        raise TypeError("band values must be numeric")
    if sar > 0.5 and surge < 1.0:
        return [{
            "conflict_id": f"{tile_ref}-sar-vs-model-01",
            "tile_ref": tile_ref,
            "claim": "SAR shows extensive water but model surge is low",
            "hazard_contradiction": f"sar_water={sar} vs model_surge_m={surge}",
            "confidence": 0.72,
            "reviewer_required": True,
        }]
    return []


def detect(tile_ref: str, bands: dict, assets: list | None = None) -> list[dict]:
    """Return data_conflicts[]; on ANY exception/API fail return [] (never blocks)."""
    try:
        return _check(tile_ref, bands, assets or [])
    except Exception:
        return []


def detect_with_client(tile_ref: str, bands: dict, assets: list | None = None,
                       client: Any = None) -> list[dict]:
    """Injectable-client variant for tests: client failure -> []."""
    try:
        if client is not None:
            client.analyze(tile_ref, bands, assets or [])  # may raise
        return _check(tile_ref, bands, assets or [])
    except Exception:
        return []
