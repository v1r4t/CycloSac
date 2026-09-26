# DEMO-SHOTS — Backup-Video Runbook (7 beats, 180s)

Runbook only; no mp4 recorded here. All values verified 2026-09-26 on
`agent/demo-verify` via TEMP-dir run
(`--inputs sample_inputs_demo --out $env:TEMP/demo-verify/forecast.json`).
Suite at time of verification: **62 passed, 3 failed**
(failures are `ModuleNotFoundError` for `scripts/` imports in
`tests/e2e/test_demo_scale.py`, `tests/unit/test_slosh.py` — pre-existing,
unrelated to pipeline output).

## Beat 1 — 0:00 T-48h replay + surge overlay (~20s)
- On screen: terminal + `dashboard/index.html` map, 2.5m surge off Puri.
- Run: `$env:PYTHONPATH='src'; python -m forecaster.cli --inputs sample_inputs_demo --out $env:TEMP/dv/forecast.json --artifacts $env:TEMP/dv/artifacts`
- Say: "T-48h replay of Michaung, category 3, landfall 27 Sep 06:00 IST."
- Proof: `01_hazard.json` → `max_depth_m: 2.5`, hazard_summary names Michaung cat 3. VERIFIED.

## Beat 2 — 0:20 Exposure (~30s)
- On screen: `02_vulnerability.json` sorted desc, coastal `in_hazard: true`.
- Run: `python -c "import json; v=json.load(open('.../02_vulnerability.json')); print(len(v))"`.
- Say: "35 assets scored: 17 substations, 4 hospitals; shelters top at 85.5."
- Proof: n=35 (17 substation, 4 hospital); top PURI-SHEL-01/02 = 85.5. VERIFIED.

## Beat 3 — 0:50 Cascade BFS + union (~30s)
- On screen: `03_cascade.json` → `cumulative_population_affected: 60000`.
- Run: show file / `python -c` print of the key.
- Say: "Triggers above 70 fan out to depth 3; ward-union population 60,000 — union, not double-counted."
- Proof: 30 triggers >70, 30 chains, cumulative 60000. Note: depth cap is 3
  (`MAX_HOPS`, `src/forecaster/config.py:5`); observed max_depth=1 in this run. VERIFIED (with note).

## Beat 4 — 1:20 Advisory, SMS-280 (~30s)
- On screen: `04_advisories.json` — `channel: sms`, short messages.
- Run: `python -c` max `len(message)`; optional `python scripts/smoke_gemini.py` (exit 2 = fallback OK).
- Say: "Glossary-grounded advisory, SMS channel capped at 280 chars."
- Proof: 5 advisories, all `sms`, max len 70 ≤ 280. Note: Odia glossary
  (`sample_inputs_demo/glossary/or.json`) loads, but this run's top-5 map to
  ndrf/power audiences so all 5 messages are `en`. VERIFIED (with note).

## Beat 5 — 1:50 Counterfactual slider (~30s)
- On screen: dashboard slider or `06_counterfactual.json`.
- Run: `cat .../06_counterfactual.json`.
- Say: "Static 2%/h evacuation: exposed drops 6000 → 5280 → 4560 → 3120, saving 2,880 at 24h."
- Proof: exact sequence + `marginal_lives_saved: 2880` at 24h. VERIFIED.

## Beat 6 — 2:20 Parametric ledger (~30s)
- On screen: `05_parametric.json` — `payout_pct: 0.4`.
- Run: show file.
- Say: "Wind 165 + surge 2.5 trips the (150, 1.5) tier: 40% on 5 insured substations, ₹20,00,000 each."
- Proof: 5 events × 0.4 × 2000000.0 (PURI-SUB-01/03/05/07/09). VERIFIED.

## Beat 7 — 2:50 Conflicts + QA (~10s)
- On screen: `forecast.json` → `data_conflicts: []`, `quality_check: pass`, exit 0.
- Run: `python -c` print of both keys; `$env:PYTHONPATH='src'; python -m pytest tests/`.
- Say: "Path2 check is annotate-only and never blocks; zero open conflicts; QA pass, zero blockers."
- Proof: `data_conflicts []`, `overall_status pass / blocker_count 0`, CLI exit 0. VERIFIED.

## Judge answers (one-liners)
- Surge synthetic because the lookup is a documented stub: bilinear table mirroring
  `surge_depth`, provenance string "synthetic stub... replace with NOAA SLOSH" —
  refs `scripts/make_slosh_lookup.py:1-8,30`, `docs/GEE.md:28-33`.
- Dispatch is blocked only by QA `block` status (exit 1) or stage errors
  (loader 2 / invariant 3 / internal 4 / GEE-no-cache 5); conflicts never block —
  refs `src/forecaster/config.py:32-37`, `src/forecaster/cli.py:67,79,124,164-172`.
