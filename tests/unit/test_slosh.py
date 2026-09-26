"""SLOSH lookup RED: npz grid loads, matches formula, missing -> fallback."""
import numpy as np
from forecaster import hazard_sim


def test_lookup_roundtrip(tmp_path):
    from make_slosh_lookup import build
    p = build(tmp_path / "slosh.npz")
    grid = hazard_sim.load_lookup(str(p))
    assert hazard_sim.surge_from_lookup(grid, 160, 980, 10.0) == \
        hazard_sim.surge_from_lookup(grid, 160, 980, 10.0)
    assert 0 <= hazard_sim.surge_from_lookup(grid, 160, 980, 10.0) <= 15


def test_lookup_matches_formula():
    from make_slosh_lookup import build
    import tempfile, os
    with tempfile.TemporaryDirectory() as t:
        p = build(os.path.join(t, "s.npz"))
        grid = hazard_sim.load_lookup(p)
        assert abs(hazard_sim.surge_from_lookup(grid, 150, 980, 10.0)
                   - hazard_sim.surge_depth(150, 980, 10.0)) < 0.3


def test_missing_lookup_fallback():
    assert hazard_sim.load_lookup("no/such/file.npz") is None
