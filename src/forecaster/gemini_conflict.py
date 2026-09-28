"""Gemini Path2 multimodal conflict detector (LLM with heuristic fallback, never blocks)."""

from __future__ import annotations

import os
import re
from typing import Any

from . import config

_VERDICT_RE = re.compile(r"conflict\s*:\s*(yes|no)", re.IGNORECASE)


def build_evidence(tile: dict, bands: dict, assets: list, met: dict | None = None) -> dict:
    """Compact multimodal evidence package passed to Gemini (metadata only, no image bytes)."""
    tile = tile or {}
    bands = bands or {}
    met = met or {}
    exposed = [{"asset_id": a.get("asset_id"), "vulnerability_score": a.get("vulnerability_score")}
               for a in (assets or [])[:10]]
    return {
        "sar": {"sar_water_frac": bands.get("sar_water", bands.get("sar_water_frac", 0))},
        "surge": {"model_surge_m": bands.get("model_surge_m", bands.get("surge_m", 0))},
        "rainfall": {"rainfall_72h_mm": bands.get("rainfall_72h_mm", 0)},
        "exposed_assets": exposed,
        "tile_metadata": {"source": tile.get("source"), "date_acquired": tile.get("date_acquired"),
                          "thumb_url": tile.get("thumb_url"), "datasets": tile.get("datasets", {})},
        "advisory_context": {"cyclone_name": met.get("cyclone_name"),
                             "intensity_kmh": met.get("intensity_kmh")},
    }


def _llm_complete(prompt: str) -> str:
    """Single Gemini call for Path2. Raises on failure (caller falls back)."""
    import google.generativeai as genai  # lazy, only when key set

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL))
    resp = model.generate_content(prompt)
    return (getattr(resp, "text", "") or "").strip()


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
        return detect_with_llm(tile_ref, bands, assets or [])
    except Exception:
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


def detect_with_llm(tile_ref: str, bands: dict, assets: list | None = None,
                    met: dict | None = None, tile: dict | None = None,
                    complete=None) -> list[dict]:
    """Gemini-backed conflict check with deterministic heuristic fallback.

    complete(prompt) overrides the LLM call (test seam). Any LLM failure
    falls back to _check(); any total failure returns [] (never blocks).
    """
    try:
        heuristic = _check(tile_ref, bands, assets or [])
    except Exception:
        return []
    try:
        pkg = build_evidence(tile or {}, bands, assets or [], met)
        prompt = ("Compare SAR water extent vs model surge using only this evidence. "
                  f"Evidence: {pkg}. Reply 'Conflict: yes/no' with one-line reason and confidence.")
        if complete is not None:
            text = complete(prompt)
            llm_used = True
        elif os.environ.get("GEMINI_API_KEY"):
            text = _llm_complete(prompt)
            llm_used = True
        else:
            raise RuntimeError("GEMINI_API_KEY not set")
        lowered = (text or "")
        m = _VERDICT_RE.search(lowered)
        verdict_yes = bool(m and m.group(1).lower() == "yes")
        if verdict_yes and heuristic:
            out = dict(heuristic[0])
            out.update({"generation_mode": "gemini",
                        "llm_model": os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL),
                        "llm_excerpt": (text or "")[:280],
                        "evidence_package": pkg})
            return [out]
        if verdict_yes:
            return [{
                "conflict_id": f"{tile_ref}-sar-vs-model-llm",
                "tile_ref": tile_ref,
                "claim": (text or "")[:280] or "LLM flagged SAR/model mismatch",
                "hazard_contradiction": f"sar={pkg['sar']} vs surge={pkg['surge']}",
                "confidence": 0.65,
                "reviewer_required": True,
                "generation_mode": "gemini",
                "llm_model": os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL),
                "evidence_package": pkg,
            }]
        flagged = []
        for c in heuristic:
            c = dict(c)
            c.update({"generation_mode": "template_heuristic",
                      "llm_model": None,
                      "llm_disagreement": True,
                      "llm_excerpt": (text or "")[:280],
                      "evidence_package": pkg})
            flagged.append(c)
        return flagged
    except Exception:
        flagged = []
        for c in heuristic:
            c = dict(c)
            c.update({"generation_mode": "template_heuristic", "llm_model": None})
            flagged.append(c)
        return flagged
