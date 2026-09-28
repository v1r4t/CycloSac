# Puri T-48h flagship replay: one command recreates all artifacts and checks
# expected headline metrics. Fails (exit 1) on any mismatch.
$ErrorActionPreference = 'Stop'
$env:PYTHONPATH = 'src'

$asOf = '2026-09-25T06:00:00+05:30'
python -m forecaster.cli --inputs sample_inputs_demo --out output/forecast.json --artifacts output/artifacts --as-of $asOf
if ($LASTEXITCODE -ne 0) { Write-Error "CLI exit=$LASTEXITCODE"; exit 1 }

python -c @"
import json, hashlib, sys
fc = json.load(open('output/forecast.json'))
checks = [
    ('assets', len(fc['vulnerability_register']), 35),
    ('in_hazard', sum(1 for r in fc['vulnerability_register'] if r.get('in_hazard')), 30),
    ('chains', len(fc['cascade_impact']['cascade_chains']), 25),
    ('union_pop', fc['cascade_impact']['cumulative_population_affected'], 421172),
    ('rain_pathways', fc['rainfall_summary']['total_pathways'], 30),
    ('advisories', len(fc['advisories']), 5),
    ('dispatch', len(fc['dispatch_records']), 5),
    ('payout_pct', fc['parametric']['payout_events'][0]['payout_pct'], 0.4),
    ('qa', fc['quality_check']['overall_status'], 'pass'),
    ('blockers', fc['quality_check']['blocker_count'], 0),
]
bad = [f'{k}: got {v}, want {w}' for k, v, w in checks if v != w]
if bad:
    print('MISMATCH:'); [print(' - ' + b) for b in bad]; sys.exit(1)
h = hashlib.md5(json.dumps(fc, sort_keys=True).encode()).hexdigest()[:8]
print(f'Puri T-48h replay OK — forecast hash={h}')
"@
if ($LASTEXITCODE -ne 0) { exit 1 }
python -m pytest tests/ -q
