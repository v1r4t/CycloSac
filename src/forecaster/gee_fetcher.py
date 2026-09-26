"""GEE fetcher: cache-first. No cache + no upstream => exit 5.

Live path: tries earthengine-api when credentials exist; any failure
falls back to the cache-first stub with a WARNING (never raises).
Tests inject ``live_fetch`` into :func:`fetch_real_or_stub` so they
never need credentials.
"""
import json
import logging
import os
from pathlib import Path
from . import config

log = logging.getLogger(__name__)

# Verified live 2026-09-26 (ee.Number(1) round-trip). Override via GEE_PROJECT.
DEFAULT_PROJECT = "cyclone-forecast-123456"

# Puri demo AOI: [minlon, minlat, maxlon, maxlat] (matches regional.json bbox).
PURI_BBOX = [85.40, 19.70, 85.75, 19.95]
DATASETS = {
    "sentinel1": "COPERNICUS/S1_GRD",  # SAR backscatter (flood extent proxy)
    "srtm": "USGS/SRTMGL1_003",  # 30m DEM (surge exposure elevation)
    "imerg": "NASA/GPM_L3/IMERG_V07",  # half-hourly precipitation
}


class GeeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.code = config.EXIT_GEE_NO_CACHE


def _has_credentials() -> bool:
    """True if live GEE auth looks possible (service-account or project)."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    if os.environ.get("GEE_PROJECT"):
        return True
    try:
        ee_key = Path.home() / ".config" / "earthengine" / "credentials"
    except RuntimeError:
        return False  # stripped env (e.g. test subprocess): no home, no creds
    return ee_key.exists()


def _try_live_fetch(aoi: str, date: str) -> dict | None:
    """One real S1 tile over the AOI. Returns tile dict or None on any failure."""
    try:
        import ee  # earthengine-api, optional
    except ImportError:
        log.warning("GEE earthengine-api not installed; using cached/stub tile")
        return None
    try:
        project = os.environ.get("GEE_PROJECT", DEFAULT_PROJECT)
        ee.Initialize(project=project)
        coords = [float(x) for x in aoi.split(",")] if "," in aoi else PURI_BBOX
        rect = ee.Geometry.Rectangle(coords)
        col = (ee.ImageCollection(DATASETS["sentinel1"])
               .filterBounds(rect)
               .filterDate("2026-09-01", "2026-09-26")
               .sort("system:time_start", False))
        n = col.size().getInfo()
        if not n:
            return None
        first = ee.Image(col.first())
        acquired = first.date().format("YYYY-MM-dd").getInfo()
        try:
            thumb = first.clip(rect).getThumbURL(
                {"bands": ["VV"], "min": -25, "max": 0, "dimensions": 512})
        except Exception:
            thumb = None
        return {
            "cached": False,
            "source": "real",
            "aoi": aoi,
            "date": date,
            "date_acquired": acquired,
            "image_count": n,
            "thumb_url": thumb,
            "project": project,
            "datasets": DATASETS,
        }
    except Exception as exc:  # auth, quota, network, bad AOI, ...
        log.warning("GEE live fetch failed (%s); using cached/stub tile", exc)
        return None


def _write_stub(c: Path, aoi: str, date: str) -> dict:
    c.mkdir(parents=True, exist_ok=True)
    data = {"cached": False, "aoi": aoi, "date": date, "note": "stub tile; replace with 1 real tile"}
    (c / "tile.json").write_text(json.dumps(data))
    return data


def fetch_real_or_stub(aoi: str, date: str, cache_dir: str,
                       use_cache_only: bool = False, live_fetch=None) -> dict:
    """Cache-first fetch with injectable live path (tests pass ``live_fetch``).

    Order: cache hit -> cache-only guard (exit 5) -> live attempt ->
    stub fallback. Never raises except GeeError when cache-only + no cache.
    """
    c = Path(cache_dir)
    tile = c / "tile.json"
    if tile.exists():
        data = json.loads(tile.read_text())
        data["cached"] = True
        return data
    if use_cache_only:
        raise GeeError(f"GEE upstream unavailable and no cache in {cache_dir}")
    fetch_fn = live_fetch if live_fetch is not None else None
    if fetch_fn is None:
        try:
            import ee  # noqa: F401 — ambient creds work; stub fallback covers failure
            fetch_fn = _try_live_fetch
        except ImportError:
            fetch_fn = _try_live_fetch if _has_credentials() else None
    if fetch_fn is not None:
        try:
            live = fetch_fn(aoi, date)
        except Exception as exc:
            log.warning("GEE live fetch failed (%s); using cached/stub tile", exc)
            live = None
        if live is not None:
            c.mkdir(parents=True, exist_ok=True)
            live.setdefault("cached", False)
            live.setdefault("source", "real")
            tile.write_text(json.dumps(live))
            return live
    return _write_stub(c, aoi, date)


def fetch(aoi: str, date: str, cache_dir: str, use_cache_only: bool = False) -> dict:
    return fetch_real_or_stub(aoi, date, cache_dir, use_cache_only=use_cache_only)
