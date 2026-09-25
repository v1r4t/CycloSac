"""Advisory: template→glossary→limit→banned-filter; fail-2 → exit 4."""
from . import config

BANNED = ["might", "could", "perhaps", "possibly", "maybe"]
PRIORITY = {"power_utility": "P0", "roads_authority": "P1", "health_department": "P0",
            "municipal_commissioner": "P0", "district_collector": "P1", "ndrf_commander": "P0"}


class AdvisoryError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.code = config.EXIT_INTERNAL
        self.code_text = "ADVISORY_PROMPT_QUALITY"


def apply_filter(message: str, attempt: int = 1, strict: bool = False) -> dict:
    words = message.split()
    clean = [w for w in words if w.lower().strip(".,") not in BANNED]
    if len(clean) < len(words) and (attempt >= 2 or strict and any(
            w.lower().strip(".,") in BANNED for w in message.split())):
        # second attempt still contains banned words
        if any(w.lower().strip(".,") in BANNED for w in message.split()):
            if attempt >= 2:
                raise AdvisoryError("banned words persist after retry")
    return {"message": " ".join(clean) if clean else "Action required.", "filtered": len(clean) != len(words)}


def render(audience: str, language: str, forecast_id: str, asset_id: str,
           glossary: dict, action: str = "Take action", channel: str = "sms") -> dict:
    limit = config.CHAR_LIMITS.get(channel, 500)
    tech = {"substation": "substation"}.copy()
    tech.update(glossary or {})
    msg = f"{action} [{forecast_id}] {asset_id} {tech.get('substation', '')}".strip()
    msg = apply_filter(msg)["message"]
    if len(msg) > limit:
        msg = msg[: limit - 3] + "..."
    return {"audience": audience, "language": language, "priority": PRIORITY.get(audience, "P2"),
            "message": msg, "asset_refs": [asset_id], "forecast_id": forecast_id,
            "recommended_action": action, "channel": channel}
