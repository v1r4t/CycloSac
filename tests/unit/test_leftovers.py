"""Leftover fixes: synthetic recipient flag, single evidence list, artifact round-trip."""
import json
from forecaster import dispatch, parametric


def test_dispatch_recipient_flagged_synthetic():
    recs = dispatch.build_records(
        [{"forecast_id": "F-1", "asset_refs": ["A-1"], "audience": "district_collector",
          "message": "Go", "channel": "sms"}], "dry-run")
    assert recs[0]["recipient_is_synthetic"] is True


def test_evidence_lists_come_from_single_source():
    ev = parametric.build_payouts(
        [{"asset_id": "A-1"}], {"wind_kmh": 165, "surge_m": 2.5},
        [{"asset_id": "A-1", "sum_insured_inr": 100, "policy_id": "P-1"}])
    rec = parametric.evidence_record(ev["payout_events"][0], {"wind_kmh": 165, "surge_m": 2.5}, "FC-1")
    assert rec["next_steps"] == ev["evidence_required"] == list(parametric.EVIDENCE_REQUIRED)


def test_gee_artifact_round_trip_keeps_fetched_at(tmp_path):
    import forecaster.cli as CLI
    from test_cli_helper import make_inputs
    inp = make_inputs(tmp_path / "in")
    out = tmp_path / "forecast.json"
    art = tmp_path / "artifacts"
    assert CLI.main(["--inputs", str(inp), "--out", str(out), "--artifacts", str(art)]) == 0
    tile = json.loads((art / "00_gee.json").read_text())
    assert "retrieved_at" not in tile
    assert tile.get("fetched_at") or tile.get("date_acquired")
    from forecaster import gee_fetcher
    prov = gee_fetcher.describe(dict(tile, cached=True, retrieved_at="2026-09-26T00:00:00+00:00"), "2026-09-25")
    assert prov["fetched_at"]
