"""Golden regression: regenerate forecast (mocked LLM path) and diff pinned fields only."""
import json
import os
import subprocess
import sys
from pathlib import Path

from test_cli_helper import make_inputs

GOLDEN = Path(__file__).with_name("forecast_golden.json")


def _extract(fc: dict) -> dict:
    return {
        "vulnerability_scores": {r["asset_id"]: r["vulnerability_score"]
                                 for r in fc["vulnerability_register"]},
        "cascade_chains": fc["cascade_impact"]["cascade_chains"],
        "blocker_count": fc["quality_check"]["blocker_count"],
        "payout_pct": [e["payout_pct"] for e in fc["parametric"]["payout_events"]],
        "exposed_pop": [c["exposed_pop"] for c in fc["counterfactual"] if "exposed_pop" in c],
    }


def test_golden_deterministic_fields(tmp_path):
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    env = dict(os.environ, PYTHONPATH="src")
    r = subprocess.run([sys.executable, "-m", "forecaster.cli", "--inputs", str(inp),
                        "--out", str(out), "--artifacts", str(tmp_path / "art")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    got = _extract(json.loads(out.read_text()))
    want = json.loads(GOLDEN.read_text())
    assert got == want
