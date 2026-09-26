"""RED: forecast.json carries gee_tile provenance block."""
import json


def test_forecast_has_gee_tile(tmp_path):
    import sys
    sys.path.insert(0, "src")
    from forecaster.cli import main
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    assert main(["--inputs", str(inp), "--out", str(out)]) == 0
    fc = json.loads(out.read_text())
    assert fc["gee_tile"]["source"] in {"real", "stub"}
    assert "date" in fc["gee_tile"]
