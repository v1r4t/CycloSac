"""Optional weather-provider adapter with an explicit fixture fallback.

The core pipeline never makes a network call unless ``--weather-url`` is
provided. This keeps demos reproducible while preserving source, freshness,
and failure details for an operational integration.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import urlopen


def _value(data: dict, *names, default=None):
    for name in names:
        if data.get(name) is not None:
            return data[name]
    return default


def normalize(data: dict, fallback: dict) -> dict:
    """Normalize a provider payload while retaining required local context."""
    return {
        "cyclone_name": _value(data, "cyclone_name", "name", default=fallback["cyclone_name"]),
        "cyclone_category": _value(data, "cyclone_category", "category", default=fallback["cyclone_category"]),
        "eta_landfall": _value(data, "eta_landfall", "landfall_time", default=fallback["eta_landfall"]),
        "intensity_kmh": _value(data, "intensity_kmh", "wind_kmh", "wind_speed_kmh", default=fallback["intensity_kmh"]),
        "forward_speed_kmh": _value(data, "forward_speed_kmh", default=fallback["forward_speed_kmh"]),
        "rainfall_72h_mm": _value(data, "rainfall_72h_mm", "rainfall_mm", default=fallback["rainfall_72h_mm"]),
        "tide_phase": _value(data, "tide_phase", default=fallback["tide_phase"]),
    }


def fetch(fixture: dict, url: str | None = None, timeout_s: int = 8) -> tuple[dict, dict]:
    """Return normalized weather and a truthful provenance record."""
    now = datetime.now(timezone.utc).isoformat()
    if not url:
        return fixture, {"mode": "fixture_replay", "source": "met.json", "fetched_at": now,
                         "freshness": "replay", "error": None}
    try:
        with urlopen(url, timeout=timeout_s) as response:  # nosec B310: user-supplied opt-in URL
            raw = json.loads(response.read().decode("utf-8"))
        payload = raw.get("data", raw) if isinstance(raw, dict) else {}
        return normalize(payload, fixture), {"mode": "live_provider", "source": url,
                                             "fetched_at": now, "freshness": "live", "error": None}
    except Exception as exc:
        return fixture, {"mode": "fixture_fallback", "source": url, "fetched_at": now,
                         "freshness": "fallback", "error": str(exc)[:180]}
