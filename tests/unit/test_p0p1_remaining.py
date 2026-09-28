"""P0/P1 remaining: Path2 LLM evidence, dispatch transitions, parametric review."""
from forecaster import gemini_conflict, dispatch, parametric


def test_path2_builds_multimodal_evidence_package():
    pkg = gemini_conflict.build_evidence(
        tile={"source": "real", "date_acquired": "2026-09-24", "thumb_url": "http://t/x",
              "datasets": {"sentinel1": "COPERNICUS/S1_GRD"}, "sar_water_frac": 0.8},
        bands={"sar_water_frac": 0.8, "model_surge_m": 0.3, "rainfall_72h_mm": 200},
        assets=[{"asset_id": "A-1", "vulnerability_score": 85}],
        met={"intensity_kmh": 165, "cyclone_name": "Michaung"})
    for k in ("sar", "surge", "rainfall", "exposed_assets", "tile_metadata", "advisory_context"):
        assert k in pkg


def test_path2_llm_success_labels_model_and_falls_back_on_failure():
    bands = {"sar_water_frac": 0.8, "model_surge_m": 0.3, "rainfall_72h_mm": 200}
    out = gemini_conflict.detect_with_llm(
        "geetile", bands, [], complete=lambda prompt: "SAR shows water; model low. Conflict: yes. Confidence high.")
    assert len(out) == 1
    assert out[0]["generation_mode"] == "gemini"
    assert out[0]["reviewer_required"] is True
    out2 = gemini_conflict.detect_with_llm(
        "geetile", bands, [], complete=lambda prompt: (_ for _ in ()).throw(RuntimeError("down")))
    assert out2[0]["generation_mode"] == "template_heuristic"


def test_dispatch_approve_ack_retry_transitions():
    recs = dispatch.build_records(
        [{"forecast_id": "F-1", "asset_refs": ["A-1"], "audience": "district_collector",
          "message": "Go", "channel": "sms"}], "dry-run")
    r = dispatch.approve(recs[0], by="collector")
    assert r["status"] == "approved_for_delivery"
    assert r["approved_by"] == "collector"
    r2 = dispatch.acknowledge(r)
    assert r2["ack"] == "acknowledged"
    r3 = dispatch.retry(r2)
    assert r3["retry_count"] == 1
    assert r3["delivery_performed"] is False


def test_parametric_review_keeps_simulated_ledger():
    ev = parametric.build_payouts(
        [{"asset_id": "A-1"}], {"wind_kmh": 165, "surge_m": 2.5},
        [{"asset_id": "A-1", "sum_insured_inr": 100, "insurer_id": "INS-1", "policy_id": "P-1"}])
    rec = parametric.review(ev["payout_events"][0], decision="approved", reviewer="insurer")
    assert rec["settlement_status"] == "simulated_approved_by_insurer"
    assert rec["approved_by"] == "insurer"
    assert ev["settlement_mode"] == "simulated"
    dl = parametric.evidence_record(ev["payout_events"][0], {"wind_kmh": 165, "surge_m": 2.5}, "FC-1")
    for k in ("hazard_inputs", "trigger_logic", "payout_pct", "next_steps"):
        assert k in dl
