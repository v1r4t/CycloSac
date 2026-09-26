# DEMO — 3-min locked script (plan Sec 7)

Total 180s. Run from repo root. Assumes `pip install -r requirements.txt` done.

## 0:00 — T-48h Michaung replay + surge overlay (20s)

```powershell
$env:PYTHONPATH='src'
python -m forecaster.cli --inputs sample_inputs --out output/forecast.json --artifacts output/artifacts
```

Say: "T-48h replay of Michaung, category 2, landfall 27 Sep 06:00 IST."
Show: `dashboard/index.html` map with surge overlay (2.0m footprint off Puri).

## 0:20 — Exposure (30s)

Say: "Exposure: substation S1 inside the 2m surge footprint, scores 80.3; hospital H1 and NH-316 outside."
Show: `output/artifacts/02_vulnerability.json` — S1 top, `in_hazard: true`.

## 0:50 — Cascade BFS + union (30s)

Say: "One trigger above 70 (S1) fans out one hop to H1 on power; ward-union population 30,000 — union, not double-counted."
Show: `output/artifacts/03_cascade.json` — `max_depth: 1`, `cumulative_population_affected: 30000`.

## 1:20 — Advisory, Telugu + English, SMS-280 (30s)

Say: "Glossary-grounded advisory, SMS channel capped at 280 chars, banned hedging words retried."
Show: `output/artifacts/04_advisories.json` — `channel: sms`, `len(message) <= 280`.

## 1:50 — Counterfactual slider 0→6→12h (30s)

Say: "Static 2%/h evacuation: exposed drops 3000 → 2640 → 2280 → 1560 at 24h."
Show: dashboard counterfactual slider, or `output/artifacts/06_counterfactual.json`.

## 2:20 — Parametric ledger (30s)

Say: "Wind 160 + surge 2.0 trips the (150, 1.5) tier: 40% payout on S1, mock INR ledger."
Show: `output/artifacts/05_parametric.json` — `payout_pct: 0.4`.

## 2:50 — Gemini conflicts, human-in-loop (10s)

Say: "Path2 multimodal check returns 2 candidate conflicts for reviewer sign-off; never blocks the forecast."
Show: `forecast.json` → `data_conflicts` panel (empty stub = zero open conflicts).

## Backup

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/unit tests/e2e tests/property tests/golden
```
