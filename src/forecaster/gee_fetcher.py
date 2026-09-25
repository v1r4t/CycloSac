"""GEE fetcher: cache-first. No cache + no upstream => exit 5."""
import json
from pathlib import Path
from . import config


class GeeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.code = config.EXIT_GEE_NO_CACHE


def fetch(aoi: str, date: str, cache_dir: str, use_cache_only: bool = False) -> dict:
    c = Path(cache_dir)
    tile = c / "tile.json"
    if tile.exists():
        return {"cached": True, **json.loads(tile.read_text())}
    if use_cache_only:
        raise GeeError(f"GEE upstream unavailable and no cache in {cache_dir}")
    # prototype: no live GEE call; write cache placeholder for demo
    c.mkdir(parents=True, exist_ok=True)
    data = {"cached": False, "aoi": aoi, "date": date, "note": "stub tile; replace with 1 real tile"}
    tile.write_text(json.dumps(data))
    return data
