# CycloSac

**Cyclone Impact & Infrastructure Vulnerability Forecaster** — a technically credible prototype that answers, within the 48–120h warning window: **what will break, where, when, and who it affects.**

CycloSac fuses satellite tiles, storm-surge / rainfall / wind footprints, ward population, infrastructure assets, and dependency graphs into a single decision-grade `forecast.json` for power utilities, roads authorities, health departments, collectors, and NDRF commanders. Built for a hackathon. Not a production disaster-management platform.

Live replay: **Cyclone Michaung → Puri (T-48h)** — 35 assets scored, 30 cascade triggers, 60,000 people in the impact union, QA `pass`.

---

## Demo in 60 seconds

```powershell
pip install -r requirements.txt
python -m http.server 8000          # serve repo root (pages need http, not file://)
python -m forecaster.cli --inputs sample_inputs_demo --out output/forecast.json --artifacts output/artifacts
```

Then open:

| Page | What it is |
|---|---|
| `http://localhost:8000/site/` | Showcase: problem statement, live stats, pipeline, replay commands |
| `http://localhost:8000/dashboard/` | Operations view: surge overlay map + legend, exposure table, cascade chains, advisory cards with copy buttons, counterfactual slider, parametric ledger, conflicts panel |

Full 3-minute script: [`DEMO.md`](DEMO.md). Backup-video shot list: [`docs/DEMO-SHOTS.md`](docs/DEMO-SHOTS.md).

## How it works

```
loader ──► gee_fetcher ──► hazard_sim/hazard ──► vuln ──► cascade ──► advisory ──► parametric ──► counterfactual ──► qa
(exit 2)     (exit 5)         (exit 3)              UTM 50m ring   BFS ≤3, union    SMS-280, LLM     wind/surge table   0/6/12/24h         12 checks
```

- **Inputs** (`loader.py`, strict pydantic): surge/rainfall/wind GeoJSON, met summary, asset register, ward population, dependency graph, audience map, glossary, regional context, insurance register.
- **Hazard** (`hazard_sim.py`, `hazard.py`): Holland wind model, documented SLOSH lookup grid (`scripts/make_slosh_lookup.py`, provenance in `docs/GEE.md`), rainfall damage index; bands-sum ±5%, timeline sorted by hours-before-landfall.
- **Vulnerability** (`vuln.py`): polygons projected to UTM 32645 and buffered 50m (never buffered points), 35/25/20/10/10 scoring against per-type fragility curves, sorted descending.
- **Cascade** (`cascade.py`): BFS from triggers ≥70, hop + dependency type carried on edges, max depth 3, ward-level population union (never summed), cycle warnings.
- **Advisories** (`advisory.py`, `gemini_path1.py`): channel-first limits (SMS 280), Odia glossary substitution, banned hedging-word filter with a second LLM sampling or exit 4. Template fallback keeps runs deterministic offline.
- **Money + what-if** (`parametric.py`, `counterfactual.py`): wind/surge payout table → mock INR ledger; static-rate evacuation horizons with monotonicity QA.
- **QA + CLI** (`qa.py`, `cli.py`): 12 deterministic checks, exact `blocker_count`, exits `0 pass · 1 QA-block · 2 loader · 3 invariant · 4 internal · 5 GEE-no-cache`, per-stage artifacts, one `forecast.json`.

## Verify it

```powershell
python -m pytest tests/                       # 66 green, ~3s, offline
python scripts/smoke_gemini.py                # exit 2 = fallback verified (no key); exit 0 = live LLM
```

- `tests/unit` — scoring, BFS, filters, QA flags, wire-through tests (CLI→Path1/Path2).
- `tests/property` — seeded invariant loops (bands, breakdowns, union ≤ sum, blocker counts).
- `tests/golden` — pins deterministic forecast fields; LLM output excluded.
- `tests/e2e` — exit-code paths 0/2/3/5 + demo-scale replay (17 substations, 4 hospitals).
- `tests/fixtures/adversarial` — boundary 49.9/50.1m, cyclic graph, overlapping wards.

## Going live (optional)

Offline defaults keep every run reproducible. For live data:

```powershell
pip install -r requirements-live.txt
$env:GEE_PROJECT='cyclone-forecast-123456'    # Earth Engine project with API enabled
$env:GEMINI_API_KEY='...'                     # AI Studio key (GEMINI_MODEL override supported)
```

GEE tile provenance: [`docs/GEE.md`](docs/GEE.md). Live runs verified: Sentinel-1 scene 2026-09-24 ×2 over Puri; Gemini prose advisories ≤280ch, QA pass.

## Scope and limits

Prototype trade-offs, stated plainly: stub SMS delivery (copy buttons only), mock single-insurer INR ledger, T-48h replay instead of realtime polling, SLOSH-geometry stub behind a documented lookup, static evacuation rate, no auth, demo-scale datasets. Deferred items live in the build spec: `C:\Users\itzdh\.opencode\plan\2026-09-25-master-forecaster-design.md`.

## Layout

```
src/forecaster/      pipeline modules (config, loader, models, gee_fetcher, hazard*, vuln,
                     cascade, glossary, advisory, gemini_path1, gemini_conflict,
                     parametric, counterfactual, qa, cli)
scripts/             make_demo_inputs, make_slosh_lookup, smoke_gemini
sample_inputs_demo/  Puri-scale replay inputs (+ live S1 tile cache)
output/              forecast.json + per-stage artifacts (committed demo evidence)
dashboard/  site/    operations view + showcase (static, zero build)
tests/               unit · e2e · property · golden · fixtures
docs/                GEE.md (tile + SLOSH provenance), DEMO-SHOTS.md (video runbook)
```

Built with Python 3.14, pydantic v2, shapely/pyproj, Leaflet. [CycloSac on GitHub](https://github.com/v1r4t/CycloSac).
