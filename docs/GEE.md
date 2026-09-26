# GEE — 1 Real Tile

## Datasets
- Sentinel-1 SAR: `COPERNICUS/S1_GRD` (flood extent proxy)
- SRTM DEM 30m: `USGS/SRTMGL1_003` (surge exposure elevation)
- IMERG precip: `NASA/GPM_L3/IMERG_V07` (rainfall input)

## AOI
Odisha coast (Michaung replay): bounding box `86.0,19.0,87.5,20.5`
(lon_min,lat_min,lon_max,lat_max). Date window: `2026-09-25`.

## Reproduce 1 real tile (judge path, ~5 min)
1. `pip install earthengine-api`
2. Auth once: `earthengine authenticate` (or set `GOOGLE_APPLICATION_CREDENTIALS`
   to a service-account key, plus `GEE_PROJECT=<project-id>`).
3. Run: `PYTHONPATH=src python -c "
   from forecaster import gee_fetcher;
   print(gee_fetcher.fetch_real_or_stub('86.0,19.0,87.5,20.5','2026-09-25','data/gee_cache'))"`
4. Verify: `data/gee_cache/tile.json` contains `"source": "real"`.
5. No credentials / offline? Same command falls back to a stub tile with a
   WARNING and the pipeline continues on cache; exit 5 only when
   `--cache-only` is passed with an empty cache.

## Design
`fetch_real_or_stub()` is cache-first; the live path is injectable
(`live_fetch=`) so unit tests never need credentials.

## SLOSH provenance
Surge lookup is a **SLOSH stub** (bilinear interpolation over a local table),
not the operational NOAA SLOSH model. Citation: Jelesnianski, Chen & Shaffer,
"SLOSH: Sea, Lake, and Overland Surges from Hurricanes" (NOAA Tech. Rep.
NWS 48, 1992). Replace `SLOSH_LOOKUP_PATH` with basin runs before any
operational use.
