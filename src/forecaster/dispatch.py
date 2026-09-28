"""Safe advisory dispatch records. External delivery is intentionally not performed."""
from __future__ import annotations

from datetime import datetime, timezone


def build_records(advisories: list[dict], mode: str = "dry-run") -> list[dict]:
    """Create auditable prepared/approved records without sending a message."""
    status = "approved_for_delivery" if mode == "approved" else "prepared_for_review"
    created_at = datetime.now(timezone.utc).isoformat()
    return [{
        "dispatch_id": f"{advisory.get('forecast_id', 'forecast')}-{index + 1:02d}",
        "asset_id": (advisory.get("asset_refs") or [None])[0],
        "audience": advisory.get("audience"),
        "recipient": f"{advisory.get('audience', 'authority')}@{(advisory.get('asset_refs') or ['district'])[0]}",
        "recipient_is_synthetic": True,
        "channel": advisory.get("channel", "sms"),
        "status": status,
        "mode": mode,
        "delivery_performed": False,
        "created_at": created_at,
        "retry_count": 0,
        "ack": "pending",
        "approved_by": "operator" if mode == "approved" else None,
        "message_hash_input": advisory.get("message", ""),
    } for index, advisory in enumerate(advisories)]


def approve(record: dict, by: str = "operator") -> dict:
    """Operator approval transition (still dry-run; never sends)."""
    out = dict(record)
    out.update({"status": "approved_for_delivery", "mode": "approved",
                "approved_by": by})
    return out


def acknowledge(record: dict) -> dict:
    out = dict(record)
    out.update({"ack": "acknowledged"})
    return out


def retry(record: dict) -> dict:
    out = dict(record)
    out.update({"retry_count": int(record.get("retry_count", 0)) + 1})
    return out
