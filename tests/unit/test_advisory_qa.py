"""Task 5 RED: advisory limits/filter/retry + QA blockers."""
import pytest
from forecaster import advisory, qa

BANNED = ["might", "could", "perhaps", "possibly", "maybe"]


def test_sms_limit_and_glossary():
    msg = advisory.render("municipal_commissioner", "or", "FC-1", "A1",
                          {"substation": "upakendra"}, action="De-energize A1 by T-24h")
    assert "FC-1" in msg["message"] and len(msg["message"]) <= 280


def test_banned_word_filtered():
    out = advisory.apply_filter("Substation might fail", attempt=1)
    assert not any(w in out["message"].lower().split() for w in BANNED)


def test_double_fail_raises_exit4():
    with pytest.raises(advisory.AdvisoryError) as e:
        advisory.apply_filter("might maybe possibly could", attempt=2, strict=True)
    assert e.value.code == 4


def test_qa_blocker_count_exact():
    flags = [{"severity": "BLOCKER", "check": "x", "field": "f", "issue": "i", "suggested_fix": "fix"},
             {"severity": "WARNING", "check": "y", "field": "g", "issue": "j", "suggested_fix": "fix"}]
    res = qa.summarize(flags)
    assert res["overall_status"] == "block" and res["blocker_count"] == 1


def test_qa_contradiction_flagged():
    reg = [{"asset_id": "A1", "in_hazard": False, "vulnerability_score": 80}]
    flags = qa.check_register(reg, {"A1"})
    assert any(f["severity"] == "BLOCKER" for f in flags)
