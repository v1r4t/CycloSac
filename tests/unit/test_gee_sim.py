"""Task 6 RED: GEE cache-first, hazard_sim bounds, glossary fail-fast."""
import json
import pytest
from forecaster import gee_fetcher, hazard_sim, glossary


def test_gee_cache_hit(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "tile.json").write_text(json.dumps({"cached": True}))
    out = gee_fetcher.fetch("AOI", "2026-09-25", str(cache), use_cache_only=True)
    assert out["cached"] is True


def test_gee_no_cache_raises_exit5(tmp_path):
    with pytest.raises(gee_fetcher.GeeError) as e:
        gee_fetcher.fetch("AOI", "2026-09-25", str(tmp_path / "empty"), use_cache_only=True)
    assert e.value.code == 5


def test_holland_bounds():
    w = hazard_sim.holland_wind(150, 50)
    assert 0 < w < 250


def test_surge_interp():
    d = hazard_sim.surge_depth(150, 980, 10.0)
    assert 0 <= d <= 15


def test_glossary_missing_raises(tmp_path):
    with pytest.raises(glossary.GlossaryError):
        glossary.load(str(tmp_path), "or")
