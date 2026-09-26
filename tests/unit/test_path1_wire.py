"""Wire-test: CLI advisory stage goes through gemini_path1.generate."""
import json


def test_cli_uses_path1(tmp_path, monkeypatch):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    seen = {}

    real_generate = CLI.gemini_path1.generate

    def spy(action, ctx):
        seen["called"] = True
        return real_generate(action, ctx)

    monkeypatch.setattr(CLI.gemini_path1, "generate", spy)
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    rc = CLI.main(["--inputs", str(inp), "--out", str(out)])
    assert rc == 0
    assert seen.get("called") is True
    fc = json.loads(out.read_text())
    assert all("llm_used" in a for a in fc["advisories"])
