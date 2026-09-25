"""E2E RED: CLI happy path exit 0 + forecast.json keys."""
import json
import subprocess
import sys


def test_cli_happy(tmp_path):
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    art = tmp_path / "art"
    r = subprocess.run([sys.executable, "-m", "forecaster.cli", "--inputs", str(inp),
                        "--out", str(out), "--artifacts", str(art)],
                       capture_output=True, text=True, env={"PYTHONPATH": "src", "PATH": __import__("os").environ["PATH"]})
    assert r.returncode == 0, r.stderr
    fc = json.loads(out.read_text())
    for k in ["forecast_id", "hazard_narrative", "vulnerability_register",
              "cascade_impact", "advisories", "quality_check"]:
        assert k in fc
