# DEMO — 3-min locked script (plan Sec 7)

Total 180s. Run from repo root. Assumes `pip install -r requirements.txt` done.

## 0:00 — T-48h Michaung replay + surge overlay (20s)

```powershell
$env:PYTHONPATH='src'
python -m forecaster.cli --inputs sample_inputs_demo --out output/forecast.json --artifacts output/artifacts
```

Say: "T-48h replay of Michaung, category 3, landfall 27 Sep 06:00 IST."
Show: `dashboard/index.html` map with 2.5m surge footprint off Puri.

## 0:20 — Exposure (30s)

Say: "35 assets scored: 17 substations, 4 hospitals; shelters top at 85.5 inside the surge strip."
Show: `output/artifacts/02_vulnerability.json` — sorted desc, `in_hazard: true` on coastal grid.

## 0:50 — Cascade BFS + union (30s)

Say: "Triggers above 70 fan out to depth 3; ward-union population 60,000 — union, not double-counted."
Show: `output/artifacts/03_cascade.json` — `cumulative_population_affected: 60000`.

## 1:20 — Advisory, Odia + English, SMS-280 (30s)

Say: "Glossary-grounded advisory (Odia), SMS channel capped at 280 chars; banned hedging words force a second LLM sampling or exit 4."
Show: `output/artifacts/04_advisories.json` — `channel: sms`, `len(message) <= 280`. Live-key? run `python scripts/smoke_gemini.py`.

## 1:50 — Counterfactual slider 0→6→12→24h (30s)

Say: "Static 2%/h evacuation: exposed drops 6000 → 5280 → 4560 → 3120, saving 2,880 at 24h."
Show: dashboard counterfactual slider, or `output/artifacts/06_counterfactual.json`.

## 2:20 — Parametric ledger (30s)

Say: "Wind 165 + surge 2.5 trips the (150, 1.5) tier: 40% on 5 insured substations, ₹20,00,000 each, mock INR ledger."
Show: `output/artifacts/05_parametric.json` — `payout_pct: 0.4`.

## 2:50 — Gemini conflicts, human-in-loop (10s)

Say: "Path2 check runs annotate-only and never blocks; this run has zero open conflicts — a SAR-vs-model mismatch would land here for reviewer sign-off."
Show: `forecast.json` → `data_conflicts` ([]) and dashboard panel.

## Backup

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/
python scripts/smoke_gemini.py  # exit 2 = fallback verified without key
```
