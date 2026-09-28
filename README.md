# CycloSac

**Cyclone Impact & Infrastructure Vulnerability Forecaster** — a technically credible prototype that answers, within the 48–120h warning window: **what will break, where, when, and who it affects.**

CycloSac fuses satellite tiles, storm-surge / rainfall / wind footprints, ward population, infrastructure assets, and dependency graphs into a single decision-grade `forecast.json` for power utilities, roads authorities, health departments, collectors, and NDRF commanders. Built for a hackathon. Not a production disaster-management platform.

Live replay: **Cyclone Michaung → Puri (T-48h)** — 35 assets scored (30 in hazard, shelters top 85.5), 25 cascade chains, 421,172 people in the ward-union impact, 30 rainfall pathways, 5 advisories with dry-run dispatch records, simulated 40% parametric payout, QA `pass`.

---

## Demo in 60 seconds

```powershell
pip install -r requirements.txt
python -m http.server 8000          # serve repo root (pages need http, not file://)
python -m forecaster.cli --inputs sample_inputs_demo --out output/forecast.json --artifacts output/artifacts --as-of 2026-09-25T06:00:00+05:30
```

Then open:

| Page | What it is |
|---|---|
| `http://localhost:8000/site/` | Showcase: problem statement, live stats, pipeline, replay commands |
| `http://localhost:8000/dashboard/` | Operations view: surge overlay map + legend, exposure table, cascade chains, advisory cards with copy buttons, counterfactual slider, parametric ledger, conflicts panel |

Full 3-minute script: [`DEMO.md`](DEMO.md). Backup-video shot list: [`docs/DEMO-SHOTS.md`](docs/DEMO-SHOTS.md).

## How it works

```
loader ──► GEE + weather provenance ──► hazard ──► vulnerability + rainfall pathways ──► cascade ──► Gemini advisory ──► dispatch record ──► parametric ──► QA
(exit 2)     (exit 5)         (exit 3)              UTM 50m ring   BFS ≤3, union    SMS-280, LLM     wind/surge table   0/6/12/24h         12 checks
```

- **Inputs + provenance** (`loader.py`, `weather_fetcher.py`, strict pydantic): surge/rainfall/wind GeoJSON, meteorological summary, asset register, ward population, dependency graph, audience map, glossary, regional context, insurance register. `--weather-url` is an opt-in live JSON adapter; every run records whether the result is live, replayed, or a fallback.
- **Hazard** (`hazard_sim.py`, `hazard.py`): Holland wind model, documented SLOSH lookup grid (`scripts/make_slosh_lookup.py`, provenance in `docs/GEE.md`), rainfall damage index; bands-sum ±5%, timeline sorted by hours-before-landfall.
- **Vulnerability + rainfall pathways** (`vuln.py`, `rainfall_pathways.py`): polygons projected to UTM 32645 and buffered 50m (never buffered points), 35/25/20/10/10 scoring against per-type fragility curves, plus explainable access/service pathways when 72-hour rainfall crosses asset-specific thresholds.
- **Cascade** (`cascade.py`): BFS from triggers ≥70, hop + dependency type carried on edges, max depth 3, ward-level population union (never summed), cycle warnings.
- **Advisories + dispatch review** (`advisory.py`, `gemini_path1.py`, `dispatch.py`): channel-first limits (SMS 280), Odia glossary substitution, evidence-grounded Gemini Flash prompting, banned hedging-word filter, and auditable dry-run/approval records. The CLI never sends messages.
- **Money + what-if** (`parametric.py`, `counterfactual.py`): wind/surge payout table → simulated INR liquidity ledger with trigger evidence and insurer-review status; static-rate evacuation horizons with monotonicity QA.
- **QA + CLI** (`qa.py`, `cli.py`): 12 deterministic checks, exact `blocker_count`, exits `0 pass · 1 QA-block · 2 loader · 3 invariant · 4 internal · 5 GEE-no-cache`, per-stage artifacts, one `forecast.json`.

## Judge narrative (60 seconds)

1. A cyclone threatens Puri district (Michaung T-48h replay).
2. GEE + weather inputs establish hazard context — every run labels source, timestamp, and live/replay/fallback/stale.
3. Surge + rainfall pathways identify infrastructure and population risk (30 pathways: 5 flooded roads, 4 hospitals, 2 shelters, 17 power assets; 421,172 ward-union pop).
4. Gemini Flash explains recommended localized authority actions with confidence + limitations; hazard math stays deterministic.
5. Authorities review and approve dry-run dispatch records (recipient, channel, retry, ack — never auto-sent).
6. Simulated parametric trigger evidence (wind 165 + surge 2.5 → 40%) enables faster liquidity review.

## Verify it

```powershell
python -m pytest tests/                       # 83 green, ~7s, offline
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
$env:GEMINI_API_KEY='...'                     # AI Studio key (defaults to gemini-3.7-flash; GEMINI_MODEL override supported)
```

GEE tile provenance: [`docs/GEE.md`](docs/GEE.md). Live runs verified: Sentinel-1 scene 2026-09-24 ×2 over Puri; Gemini prose advisories ≤280ch, QA pass.

## Scope and limits

Prototype trade-offs, stated plainly: dispatch records are dry-run/approval states (no SMS is sent), the insurer ledger is simulated, and the default scenario is a T-48h replay. A live weather URL and GEE credentials are opt-in; failures fall back visibly to replay inputs. SLOSH geometry remains a documented lookup stub, evacuation rate is static, there is no auth, and datasets are demo scale.

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
