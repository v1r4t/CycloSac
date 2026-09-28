# GEE — 1 Real Tile

## Datasets
- Sentinel-1 SAR: `COPERNICUS/S1_GRD` (flood extent proxy)
- SRTM DEM 30m: `USGS/SRTMGL1_003` (surge exposure elevation)
- IMERG precip: `NASA/GPM_L3/IMERG_V07` (rainfall input)

## AOI
Puri city (Michaung replay): bounding box `85.78,19.78,85.95,19.92`
(lon_min,lat_min,lon_max,lat_max) — temple, station, DHH hospital, NH-316.
Date window: `2026-09-25`. Earlier rural-Chilika AOI retired 2026-09-27 after
the structures-on-water finding.

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
(`live_fetch=`) so unit tests never need credentials. Every tile is
summarized by `gee_fetcher.describe(tile, as_of)`: `mode` in
{`live_provider`, `cached_replay`, `fixture_fallback`}, `freshness` in
{`live`, `replay`, `fallback`, `stale`} (stale = `date_acquired` more
than 3 days before `--as-of`), mirroring the `weather_fetcher`
vocabulary. `output/artifacts/00_gee.json` omits only the per-read
`retrieved_at` timestamp; stub tiles carry `date_acquired` (= request
date) and `fetched_at` so reloaded caches keep their provenance.

## Live traffic overlay (optional, annotate-only)

- Provider: TomTom Traffic Flow v4 (`flowSegmentData`, absolute), 3 probes on
  Puri arterials (`traffic_overlay.PROBE_POINTS`); HERE documented fallback.
- Enable: `TOMTOM_API_KEY=... python -m forecaster.cli --traffic on ...`.
  Default off. Missing key, no coverage, timeout, bad payload → `[]` with a
  WARNING; pipeline exits and QA verdicts never change on traffic.
- Output: `forecast.json: traffic_overlay[]` + `07_traffic.json`; dashboard
  "Live Traffic" layer appears only when segments exist, else the legend
  reads "no data — validated core only".

## Population provenance (real, not fixture)

- Source: `JRC/GHSL/P2023A/GHS_POP/2020` (100m) via live GEE, fetched 2026-09-27.
- Why GHSL not WorldPop: WorldPop direct downloads returned 403/404/500 from
  this network; GHSL is the same evidence class. Revisit if WorldPop recovers.
- Method: `scripts/fetch_ghsl_pop.py [inputs] --apply` — `reduceRegions(sum,
  scale=100)` over `wards.geojson` quadrants. Sea/no-data pixels carry large
  negative codes in this epoch and are masked to 0 (W2 covers open Bay water).
- Result: W1 20,799 · W2 83,849 · W3 85,225 · W4 122,852 (total 312,725).
  Vintage 2020 estimates — NOT live headcounts; no open feed provides those.
- Provenance rides with the forecast: `population_source.json` →
  `forecast.json: population_source` → dashboard cascade card.

## SLOSH provenance
Surge lookup is a **SLOSH stub** (nearest-grid lookup over a local table
built by `scripts/make_slosh_lookup.py`, loaded from `SLOSH_LOOKUP_PATH`
=`data/slosh_lookup.npz`),
not the operational NOAA SLOSH model. Citation: Jelesnianski, Chen & Shaffer,
"SLOSH: Sea, Lake, and Overland Surges from Hurricanes" (NOAA Tech. Rep.
NWS 48, 1992). Replace `SLOSH_LOOKUP_PATH` with basin runs before any
operational use.
