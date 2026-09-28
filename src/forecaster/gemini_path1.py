"""Path1 prose: LLM-backed render with deterministic template fallback.

Thin wrapper over advisory.render. Calls google-generativeai ONLY if
GEMINI_API_KEY is set; otherwise falls back to the template render.
Never imports google-generativeai at module import time (keeps core
dependency-free and tests offline).
"""
import os

from . import advisory, config


def _apply_glossary(text: str, glossary: dict) -> str:
    if not glossary:
        return text
    out = text
    for k, v in glossary.items():
        out = out.replace(k, str(v))
    return out


def _template_raw(action: str, ctx: dict) -> str:
    forecast_id = ctx.get("forecast_id", "")
    asset_id = ctx.get("asset_id", "")
    glossary = ctx.get("glossary") or {}
    tech = {"substation": "substation"}
    tech.update(glossary)
    return f"{action} [{forecast_id}] {asset_id} {tech.get('substation', '')}".strip()


def llm_complete(prompt: str, action: str, ctx: dict) -> str:
    """Single LLM invocation. Raises on failure (caller falls back)."""
    import google.generativeai as genai  # lazy, only when key is set

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL))
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", "") or ""
    return text.strip() or _template_raw(action, ctx)


def _build_prompt(action: str, ctx: dict) -> str:
    evidence = ctx.get("evidence") or {}
    return (
        f"Write a {ctx.get('channel', config.CHANNEL_DEFAULT)} emergency advisory "
        f"({ctx.get('language', 'en')}) for {ctx.get('audience', '')} "
        f"[{ctx.get('forecast_id', '')}] asset {ctx.get('asset_id', '')}. "
        f"Action: {action}. Evidence: {evidence}. "
        "Use only the provided evidence. State the action first, use plain terms, and do not hedge."
    )


def _explain(evidence: dict) -> dict:
    """Operator-facing why + confidence + limits. Hazard math stays deterministic."""
    ev = evidence or {}
    has_surge = ev.get("surge_depth_m") is not None or ev.get("surge_bands_m") is not None
    has_rain = ev.get("rainfall_72h_mm") is not None
    has_score = ev.get("vulnerability_score") is not None
    filled = sum([has_surge, has_rain, has_score])
    confidence = "high" if filled >= 3 else "medium" if filled == 2 else "low"
    parts = []
    if ev.get("surge_depth_m") is not None:
        parts.append(f"surge {ev['surge_depth_m']}m")
    if ev.get("surge_bands_m") is not None:
        parts.append(f"bands {ev['surge_bands_m']}")
    if ev.get("rainfall_72h_mm") is not None:
        parts.append(f"rain {ev['rainfall_72h_mm']}mm/72h")
    if ev.get("vulnerability_score") is not None:
        parts.append(f"score {ev['vulnerability_score']}")
    if ev.get("gee_source"):
        parts.append(f"GEE {ev['gee_source']}")
    if ev.get("weather_mode"):
        parts.append(f"weather {ev['weather_mode']}")
    explanation = ("Recommended from " + ", ".join(parts)) if parts else "Recommended from available evidence."
    limitations = ("Hazard math is deterministic; LLM only drafts prose. "
                   "Verify with operator review, especially on stale/fallback inputs.")
    return {"explanation": explanation, "confidence": confidence,
            "limitations": limitations, "hazard_math_deterministic": True}


def generate(action: str, ctx: dict, _complete=None) -> dict:
    """Render an advisory card via LLM (if key set) else template fallback.

    _complete(action, ctx, attempt) overrides the LLM call (test seam;
    counts as LLM path). Retry: banned-word hit on attempt 1 triggers a
    second invocation; banned words persisting on attempt 2 raise
    AdvisoryError (exit 4, ADVISORY_PROMPT_QUALITY).
    """
    audience = ctx.get("audience", "")
    language = ctx.get("language", "en")
    forecast_id = ctx.get("forecast_id", "")
    asset_id = ctx.get("asset_id", "")
    glossary = ctx.get("glossary") or {}
    channel = ctx.get("channel", config.CHANNEL_DEFAULT)
    limit = config.CHAR_LIMITS.get(channel, 500)

    key_set = bool(os.environ.get("GEMINI_API_KEY"))
    use_llm = _complete is not None or key_set
    if not use_llm:
        out = advisory.render(audience, language, forecast_id, asset_id,
                              glossary, action=action, channel=channel)
        out["truncated"] = False
        out["llm_used"] = False
        out["generation_mode"] = "template_fallback"
        out["llm_model"] = None
        out["evidence_summary"] = ctx.get("evidence") or {}
        out.update(_explain(ctx.get("evidence") or {}))
        return out

    live_used = _complete is not None

    def _raw(attempt: int) -> str:
        nonlocal live_used
        if _complete is not None:
            return _complete(action, ctx, attempt)
        try:
            raw = llm_complete(_build_prompt(action, ctx), action, ctx)
            live_used = True
            return raw
        except Exception:
            live_used = False
            return _template_raw(action, ctx)

    last_clean = None
    for attempt in (1, 2):
        raw = _apply_glossary(_raw(attempt) or "", glossary)
        has_banned = any(
            w.lower().strip(".,") in advisory.BANNED for w in raw.split())
        if has_banned:
            if attempt == 1:
                continue  # second LLM invocation, new sampling
            advisory.apply_filter(raw, attempt=2, strict=True)  # raises exit 4
        last_clean = advisory.apply_filter(raw, attempt=attempt)["message"]
        break

    msg = last_clean if last_clean is not None else ""
    if not msg:
        msg = "Action required."
    truncated = False
    if len(msg) > limit:
        msg = msg[: limit - 3] + "..."
        truncated = True
    return {"audience": audience, "language": language,
            "priority": advisory.PRIORITY.get(audience, "P2"),
            "message": msg, "asset_refs": [asset_id], "forecast_id": forecast_id,
            "recommended_action": action, "channel": channel,
            "truncated": truncated, "llm_used": live_used,
            "generation_mode": "gemini" if live_used else "template_fallback",
            "llm_model": os.environ.get("GEMINI_MODEL", config.GEMINI_MODEL) if live_used else None,
            "evidence_summary": ctx.get("evidence") or {},
            **_explain(ctx.get("evidence") or {})}
