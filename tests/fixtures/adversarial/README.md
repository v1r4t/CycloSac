# Adversarial fixtures (plan Sec 4)

Small JSON inputs, each with an `expected` exit/flag block. Apply against the
prototype pipeline or call the stage function directly:

- `boundary_49_9_50_1.json` — QA contradiction threshold (`in_hazard=false`
  + score>50 = BLOCKER). B1 (49.9) clean, B2 (50.1) one BLOCKER
  `contradiction` flag. Full CLI exit: **1** (QA block).
- `cyclic_dependency.json` — A1->A2->A1 cycle. `cascade.build` must terminate,
  emit `critical_paths: ["cycle detected at A1 ..."]`, one chain. Exit **0**.
- `overlapping_wards.json` — A1+A2 share W1. `cumulative_population_affected`
  must be ward-union **1500**, not asset-sum 2500. Exit **0**.

Quick check (PYTHONPATH=src):

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/property tests/golden -v
python -c "from forecaster import cascade; import json; f=json.load(open('tests/fixtures/adversarial/cyclic_dependency.json')); print(cascade.build(f['input']['register'], f['input']['dependencies']))"
```
