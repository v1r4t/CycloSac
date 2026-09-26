# CycloSac
Technically credible prototype of the complete cyclone decision pipeline (MASTER-FORECASTER-1.1.0). Not a production platform.

## Run (Windows PowerShell)
```powershell
pip install -r requirements.txt
pip install -r requirements-live.txt  # only for live GEE tile + live Gemini; offline demo skips this
$env:PYTHONPATH='src'
python -m forecaster.cli --inputs sample_inputs --out output/forecast.json --artifacts output/artifacts
python -m pytest tests/
```
Open `dashboard/index.html` (serve repo root so it can fetch `output/forecast.json`, e.g. `python -m http.server`) — map, exposure, cascade, advisories with copy buttons, counterfactual slider, parametric ledger, conflicts panel.

## Pipeline
`loader (exit 2)` → `gee_fetcher cache-first (exit 5)` → `hazard_sim + hazard validate (exit 3)` → `vuln UTM-32645 50m buffer-ring` → `cascade BFS≤3 ward-union` → `glossary` → `advisory SMS-280 banned-filter (exit 4 on 2nd fail)` → `parametric` → `counterfactual` → `qa blockers` → `forecast.json (exit 0 pass / 1 QA-block)`.

## Scope
Must work: 1 real GEE tile slot (stub cache + `--cache-only` proves exit 5), T-48h replay, surge+rain sim stubs, vuln map, cascade viz, Gemini advisory Path1, counterfactual slider, parametric mock-INR ledger, dashboard. Mocked: SMS delivery (copy only), insurer rails, polling, perfect physics (SLOSH stub+Holland), full evac opt (static 2%/h), auth, scale.

## Hardening (tests-only, no src changes)
- `tests/property/test_invariants.py` — seeded stdlib-random loops: bands-sum 5%, breakdown-sum ±5, union ≤ sum, blocker_count exact. `python -m pytest tests/property tests/golden -v`
- `tests/golden/` — `forecast_golden.json` pins `vulnerability_scores, cascade_chains, blocker_count, payout_pct, exposed_pop`; `test_golden.py` regenerates via CLI and diffs those fields only.
- `tests/fixtures/adversarial/` — `boundary_49_9_50_1` (exit 1 QA block), `cyclic_dependency` (exit 0, cycle noted), `overlapping_wards` (exit 0, union 1500); expectations in its README.
- `DEMO.md` — 3-min locked demo script (timestamps + commands).
