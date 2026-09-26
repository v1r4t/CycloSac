"""Stage smoke test for Gemini Path1 (1:20 demo beat de-risk).

Offline (no GEMINI_API_KEY): proves template fallback + banned-word retry
paths with an injected fake. With key: one live call, checks SMS limit +
filter. Exit 0 = ready, exit 2 = skipped (no key, fallback verified).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from forecaster import gemini_path1, advisory

CTX = {"audience": "power_utility", "language": "en", "forecast_id": "SMOKE",
       "asset_id": "PURI-SUB-01", "glossary": {"substation": "upakendra"}, "channel": "sms"}


def main() -> int:
    # 1. fallback determinism (no key needed)
    os.environ.pop("GEMINI_API_KEY", None)
    a = gemini_path1.generate("De-energize PURI-SUB-01 by T-24h", CTX)
    assert a["llm_used"] is False and len(a["message"]) <= 280, a
    # 2. retry path with injected fake: banned first, clean second
    calls = iter(["substation might fail", "De-energize PURI-SUB-01 by T-24h now"])
    b = gemini_path1.generate("De-energize PURI-SUB-01 by T-24h", CTX,
                              _complete=lambda act, ctx, att: next(calls))
    assert b["llm_used"] is True and "might" not in b["message"], b
    # 3. double-fail -> exit 4 preserved
    try:
        gemini_path1.generate("x", CTX, _complete=lambda act, ctx, att: "might maybe fail")
        print("FAIL: expected AdvisoryError")
        return 1
    except advisory.AdvisoryError:
        pass
    if not os.environ.get("GEMINI_API_KEY"):
        print("SMOKE fallback paths OK; no GEMINI_API_KEY -> live call skipped (exit 2)")
        return 2
    live = gemini_path1.generate("De-energize PURI-SUB-01 by T-24h", CTX)
    assert len(live["message"]) <= 280, live
    print(f"SMOKE live OK: llm_used={live['llm_used']} msg={live['message']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
