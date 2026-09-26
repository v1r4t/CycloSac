"""Demo-scale RED: Puri-scale inputs validate + CLI exit 0."""
import json


def test_demo_scale(tmp_path):
    from make_demo_inputs import build
    d = build(tmp_path / "demo")
    assets = json.loads((d / "assets.json").read_text())
    kinds = [a["asset_type"] for a in assets]
    assert kinds.count("substation") == 17
    assert kinds.count("hospital") == 4
    assert len(assets) >= 30
    import sys
    sys.path.insert(0, "src")
    from forecaster.cli import main
    rc = main(["--inputs", str(d), "--out", str(tmp_path / "fc.json")])
    assert rc == 0
    fc = json.loads((tmp_path / "fc.json").read_text())
    assert len(fc["vulnerability_register"]) == len(assets)
    assert fc["cascade_impact"]["cumulative_population_affected"] > 0
