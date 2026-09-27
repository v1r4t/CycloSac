"""RED: traffic overlay never blocks; normalized segments via injectable fetch."""
from forecaster import traffic_overlay as T


def test_no_key_returns_empty():
    assert T.fetch("bbox", api_key=None) == []


def test_failure_returns_empty():
    def boom(url, timeout):
        raise TimeoutError("no net")
    assert T.fetch("bbox", api_key="K", _get=boom) == []


def test_normalizes_segments():
    def fake(url, timeout):
        return {"flowSegmentData": {"currentSpeed": 12, "freeFlowSpeed": 40}}
    segs = T.fetch("bbox", api_key="K", _get=fake)
    assert segs[0]["congestion"] == 0.7
    assert segs[0]["closed"] is False
