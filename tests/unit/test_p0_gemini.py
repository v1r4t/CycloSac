"""P0-2: Gemini operator explanation, confidence, limitations, evidence."""
from forecaster import gemini_path1


def test_template_fallback_carries_explanation_and_limits():
    ctx = {"audience": "district_collector", "language": "en", "forecast_id": "F-1",
           "asset_id": "A-1", "glossary": {}, "channel": "sms",
           "evidence": {"surge_depth_m": 2.5, "rainfall_72h_mm": 180}}
    out = gemini_path1.generate("Secure A-1 by T-24h", ctx)
    assert out["generation_mode"] == "template_fallback"
    assert "explanation" in out and out["explanation"]
    assert "confidence" in out and "limitations" in out
    assert out["hazard_math_deterministic"] is True


def test_llm_path_carries_model_and_explanation():
    ctx = {"audience": "district_collector", "language": "en", "forecast_id": "F-1",
           "asset_id": "A-1", "glossary": {}, "channel": "sms",
           "evidence": {"surge_depth_m": 2.5}}
    out = gemini_path1.generate("Do X", ctx,
                                _complete=lambda a, c, attempt: "De-energize A-1 by T-24h now")
    assert out["llm_used"] is True
    assert out["explanation"]
    assert out["confidence"] in ("high", "medium", "low")
