"""Live-traffic overlay (TomTom, annotate-only, never blocks).

Default off. Missing key, no coverage, timeout, bad payload → [] so the
pipeline and dashboard degrade to the validated core. HERE documented as
fallback in docs; wire only if TomTom coverage disappoints on stage.
"""
import json
import logging
import urllib.request

log = logging.getLogger(__name__)

# Sample probes on arterial corridors inside the Puri AOI (override via args).
# Verified routable 2026-09-27 (zoom-10 flow tiles); points east of ~85.55
# fall off-network (sea/rural) and 400 — kept out deliberately.
PROBE_POINTS = [(19.79, 85.50), (19.798, 85.525), (19.812, 85.54)]


def _get(url: str, timeout: float):
    req = urllib.request.Request(url, headers={"User-Agent": "CycloSac/1.0"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def _flow_url(lat: float, lon: float, key: str) -> str:
    return (f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            f"?point={lat},{lon}&key={key}")


def fetch(aoi: str, api_key: str | None = None, _get=_get,
          points: list | None = None, timeout: float = 10.0) -> list:
    """Return [{road_id, lat, lon, speed, freeflow, congestion, closed}]."""
    if not api_key:
        return []
    out = []
    try:
        for i, (lat, lon) in enumerate(points or PROBE_POINTS):
            try:
                body = _get(_flow_url(lat, lon, api_key), timeout)
                seg = (body.get("flowSegmentData") or {})
                speed = float(seg.get("currentSpeed", 0) or 0)
                free = float(seg.get("freeFlowSpeed", 0) or 0)
                congestion = round(max(0.0, min(1.0, 1 - speed / free)), 2) if free > 0 else 0.0
                out.append({"road_id": f"TOMTOM-{i+1}", "lat": lat, "lon": lon,
                            "speed": speed, "freeflow": free,
                            "congestion": congestion, "closed": False})
            except Exception as exc:
                log.warning("traffic probe %s failed: %s", i, exc)
    except Exception as exc:
        log.warning("traffic overlay failed (%s); degrading to core", exc)
        return []
    return out
