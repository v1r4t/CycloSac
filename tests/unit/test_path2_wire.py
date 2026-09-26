"""Path2 wiring RED: CLI data_conflicts reflect detector output, never block."""
import json


def test_cli_wires_path2(tmp_path, monkeypatch):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    marker = [{"conflict_id": "T-sar-vs-model-01", "tile_ref": "T",
               "claim": "SAR vs model", "hazard_contradiction": "x",
               "confidence": 0.7, "reviewer_required": True}]
    monkeypatch.setattr(CLI.gemini_conflict, "detect", lambda *a, **k: marker)
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    assert CLI.main(["--inputs", str(inp), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["data_conflicts"] == marker


def test_cli_path2_failure_never_blocks(tmp_path, monkeypatch):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs

    def boom(*a, **k):
        raise RuntimeError("api down")

    monkeypatch.setattr(CLI.gemini_conflict, "detect", boom)
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    assert CLI.main(["--inputs", str(inp), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["data_conflicts"] == []
