"""Land guard: SRTM elevation per asset; snap offshore assets west to land.

Usage: python scripts/check_land.py sample_inputs_demo [--snap]
  No args after dir: prints per-asset elevation + WATER/land flags (exit 1 if any WATER).
  --snap: nudges WATER assets west in ~200m steps until elevation > 0,
          rewrites assets.json, prints displacements. Then re-run CLI + DEMO checks.
Live GEE required (uses the verified cyclone-forecast-123456 project).
"""
import json
import os
import sys
from pathlib import Path


def elevations(assets: list, project: str | None = None) -> dict:
    import ee
    ee.Initialize(project=project or os.environ.get("GEE_PROJECT", "cyclone-forecast-123456"))
    srtm = ee.Image("USGS/SRTMGL1_003")
    feats = [ee.Feature(ee.Geometry.Point([a["lon"], a["lat"]]), {"id": a["asset_id"]})
             for a in assets]
    got = srtm.sampleRegions(collection=ee.FeatureCollection(feats),
                             scale=30, geometries=False).getInfo()
    return {f["properties"]["id"]: f["properties"].get("elevation", -999)
            for f in got["features"]}


def snap_to_land(assets: list, project: str | None = None, step: float = 0.002,
                 tries: int = 40) -> list:
    """Return (asset_id, old_lon, new_lon, elev) for snapped assets; edits in place."""
    import ee
    ee.Initialize(project=project or os.environ.get("GEE_PROJECT", "cyclone-forecast-123456"))
    srtm = ee.Image("USGS/SRTMGL1_003")
    moved = []
    for a in assets:
        pt = ee.Geometry.Point([a["lon"], a["lat"]])
        e = srtm.sample(pt, 30).first().get("elevation").getInfo()
        if e is not None and e > 0:
            continue
        old = a["lon"]
        for _ in range(tries):
            a["lon"] = round(a["lon"] - step, 5)
            pt = ee.Geometry.Point([a["lon"], a["lat"]])
            e = srtm.sample(pt, 30).first().get("elevation").getInfo()
            if e is not None and e > 0:
                break
        moved.append((a["asset_id"], old, a["lon"], e))
    return moved


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    d = Path(argv[0] if argv else "sample_inputs_demo")
    assets = json.loads((d / "assets.json").read_text())
    if "--snap" in argv:
        moved = snap_to_land(assets)
        (d / "assets.json").write_text(json.dumps(assets, indent=1))
        for m in moved:
            print(f"SNAPPED {m[0]}: lon {m[1]} -> {m[2]} (elev {m[3]})")
        print(f"snapped {len(moved)}/{len(assets)}")
        return 0
    elev = elevations(assets)
    bad = 0
    for a in assets:
        e = elev.get(a["asset_id"], -999)
        ok = e is not None and e > 0
        bad += not ok
        print(f"{a['asset_id']} {a['lat']},{a['lon']} elev={e} {'land' if ok else 'WATER'}")
    print(f"{bad} WATER / {len(assets)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
