from forecaster.gemini_conflict import detect, detect_with_client


class _FailClient:
    def analyze(self, *a, **k):
        raise RuntimeError("API down")


def test_flags_sar_vs_model():
    out = detect("tile/9/1/2", {"sar_water": 0.8, "model_surge_m": 0.3}, [])
    assert len(out) == 1
    c = out[0]
    assert c["tile_ref"] == "tile/9/1/2"
    assert c["reviewer_required"] is True
    for k in ("conflict_id", "claim", "hazard_contradiction", "confidence"):
        assert k in c


def test_no_conflict_when_agree():
    assert detect("t", {"sar_water": 0.1, "model_surge_m": 0.2}, []) == []


def test_api_fail_returns_empty():
    out = detect_with_client("t", {"sar_water": 0.9, "model_surge_m": 0.1}, [],
                             client=_FailClient())
    assert out == []
    assert detect("t", "bad-bands", []) == []
