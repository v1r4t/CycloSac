"""Exit-code + golden regression: 2 loader, 3 bands, 5 gee-no-cache, golden pins."""
import json
import subprocess
import sys
import os
from pathlib import Path
from test_cli_helper import make_inputs


def _run(inp, out, extra=None):
    env = dict(os.environ, PYTHONPATH="src")
    cmd = [sys.executable, "-m", "forecaster.cli", "--inputs", str(inp), "--out", str(out)]
    if extra:
        cmd += extra
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_exit_2_malformed(tmp_path):
    inp = make_inputs(tmp_path / "in")
    bad = json.loads((inp / "assets.json").read_text())
    del bad[0]["asset_type"]
    (inp / "assets.json").write_text(json.dumps(bad))
    r = _run(inp, tmp_path / "o.json")
    assert r.returncode == 2


def test_exit_3_bands_off(tmp_path):
    inp = make_inputs(tmp_path / "in")
    fc = json.loads((inp / "surge.geojson").read_text())
    fc["features"][0]["properties"]["depth_m"] = 99.0
    (inp / "surge.geojson").write_text(json.dumps(fc))
    r = _run(inp, tmp_path / "o.json")
    assert r.returncode == 3


def test_exit_5_gee_no_cache(tmp_path):
    inp = make_inputs(tmp_path / "in")
    r = _run(inp, tmp_path / "o.json", ["--cache-only"])
    assert r.returncode == 5


def test_golden_pins(tmp_path):
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    r = _run(inp, out)
    assert r.returncode == 0
    fc = json.loads(out.read_text())
    assert fc["vulnerability_register"][0]["vulnerability_score"] >= fc["vulnerability_register"][-1]["vulnerability_score"]
    assert fc["quality_check"]["blocker_count"] == sum(1 for f in fc["quality_check"]["flags"] if f["severity"] == "BLOCKER")
    assert fc["cascade_impact"]["cumulative_population_affected"] >= 0
    assert all(0 <= p["payout_pct"] <= 1 for p in fc["parametric"]["payout_events"])
