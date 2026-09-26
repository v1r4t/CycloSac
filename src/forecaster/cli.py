"""CLI: full pipeline with exits 0-5, artifacts, structured stderr logging."""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config
from .loader import load_inputs, LoaderError
from .gee_fetcher import fetch as gee_fetch, GeeError
from .hazard import validate_hazard, StageError
from . import vuln, cascade, glossary, advisory, gemini_path1, gemini_conflict, parametric, counterfactual, qa
from .glossary import GlossaryError


def log(level, stage, code, message, context=None):
    print(json.dumps({"level": level, "stage": stage, "code": code,
                      "message": message, "context": context or {}}), file=sys.stderr)


def write_error(artifacts, stage, err, verbose=False):
    if not artifacts:
        return
    p = Path(artifacts)
    p.mkdir(parents=True, exist_ok=True)
    body = {"stage": stage, "error_type": type(err).__name__, "error_message": str(err),
            "traceback": traceback.format_exc() if verbose else ""}
    (p / f"{stage}_error.json").write_text(json.dumps(body, indent=2))


def write_stage(artifacts, name, obj):
    if not artifacts:
        return
    p = Path(artifacts)
    p.mkdir(parents=True, exist_ok=True)
    (p / name).write_text(json.dumps(obj, indent=2, default=str))


def geojson_polys(fc, key):
    out = []
    for f in (fc or {}).get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon":
            props = f.get("properties", {})
            out.append({"polygon": g["coordinates"][0], key: props.get(key, 0)})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--crs", default=config.DEFAULT_CRS)
    ap.add_argument("--artifacts", default=None)
    ap.add_argument("--gemini-conflict-mode", default="on", choices=["off", "on"])
    ap.add_argument("--cache-only", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    ist = timezone(timedelta(hours=5, minutes=30))
    try:
        inp = load_inputs(a.inputs)
    except LoaderError as e:
        log("error", "loader", "LOADER_FAIL", str(e), {})
        write_error(a.artifacts, "00_loader", e, a.verbose)
        return config.EXIT_LOADER_FAIL
    except GlossaryError as e:
        log("error", "glossary", "GLOSSARY_MISSING", str(e), {})
        write_error(a.artifacts, "00_loader", e, a.verbose)
        return config.EXIT_LOADER_FAIL
    try:
        # GEE (priority 1)
        try:
            tile = gee_fetch("aoi", "2026-09-25", str(Path(a.inputs) / ".geecache"), use_cache_only=a.cache_only)
        except GeeError as e:
            log("error", "gee_fetcher", "GEE_NO_CACHE", str(e), {})
            write_error(a.artifacts, "00_gee", e, a.verbose)
            return config.EXIT_GEE_NO_CACHE
        write_stage(a.artifacts, "00_gee.json", tile)
        # Hazard narrative from met + footprint stats
        surge = geojson_polys(inp.raw.get("surge.geojson"), "depth_m")
        rain = geojson_polys(inp.raw.get("rainfall.geojson"), "depth_m")
        wind = geojson_polys(inp.raw.get("wind.geojson"), "wind_kmh")
        max_depth = max([s["depth_m"] for s in surge] + [0])
        narrative = validate_hazard({
            "hazard_summary": f"{inp.met.cyclone_name} cat {inp.met.cyclone_category} landfall {inp.met.eta_landfall}",
            "inundation_area_km2": 100.0, "depth_bands": [60.0, 40.0],
            "max_depth_m": max_depth,
            "timeline": [{"hours_before_landfall": 48, "event": "surge arrival"},
                         {"hours_before_landfall": 24, "event": "peak wind"},
                         {"hours_before_landfall": 0, "event": "landfall"}]})
        write_stage(a.artifacts, "01_hazard.json", narrative)
        # Vuln
        assets = [x.model_dump() for x in inp.assets]
        reg = vuln.score_assets(assets, surge, rain, wind, crs=a.crs)
        write_stage(a.artifacts, "02_vulnerability.json", reg)
        # Cascade with ward union (map all assets to W1/W2 round-robin for prototype)
        wards = inp.wards
        award = {x["asset_id"]: wards[i % len(wards)].ward_code for i, x in enumerate(reg)} if wards else {}
        wpop = {w.ward_code: w.population for w in wards}
        casc = cascade.build(reg, [d.model_dump() for d in inp.dependencies],
                             asset_ward=award, ward_pop=wpop)
        write_stage(a.artifacts, "03_cascade.json", casc)
        # Glossary + advisories (priority 6)
        lang = inp.regional.primary_language
        try:
            gloss = glossary.load(a.inputs, lang)
        except GlossaryError:
            gloss = {}
        advs = []
        for r in reg[:5]:
            aud = inp.audience.get(r["asset_id"], "district_collector")
            action = (f"De-energize {r['asset_id']} by T-24h" if "substation" in r["asset_type"]
                      else f"Secure {r['asset_id']} by T-24h")
            ctx = {"audience": aud, "language": "en" if aud != "municipal_commissioner" else lang,
                   "forecast_id": inp.regional.forecast_id, "asset_id": r["asset_id"],
                   "glossary": gloss, "channel": "sms"}
            try:
                advs.append(gemini_path1.generate(action, ctx))
            except advisory.AdvisoryError as e:
                log("error", "advisory", "ADVISORY_PROMPT_QUALITY", str(e), {"asset": r["asset_id"]})
                write_error(a.artifacts, "advisory", e, a.verbose)
                return config.EXIT_INTERNAL
        write_stage(a.artifacts, "04_advisories.json", advs)
        # Parametric (priority 8)
        par = parametric.build_payouts([{"asset_id": r["asset_id"]} for r in reg],
                                       {"wind_kmh": inp.met.intensity_kmh, "surge_m": max_depth},
                                       inp.insurance)
        write_stage(a.artifacts, "05_parametric.json", par)
        # Counterfactual (priority 7)
        base_pop = sum(w.population for w in wards) // 10
        cf = counterfactual.build(base_pop, len(casc["cascade_chains"]))
        write_stage(a.artifacts, "06_counterfactual.json", cf)
        # Gemini Path2: annotate only, never blocks (off => skip)
        if a.gemini_conflict_mode == "off":
            conflicts = []
        else:
            try:
                bands = {"sar_water_frac": tile.get("sar_water_frac", 0),
                         "model_surge_m": max_depth}
                conflicts = gemini_conflict.detect("geetile", bands, assets)
            except Exception as e:
                log("warning", "gemini_conflict", "CONFLICT_DEGRADED", str(e), {})
                conflicts = []
        # QA
        known = {x["asset_id"] for x in assets}
        flags = (qa.check_register(reg, known) + qa.check_advisories(advs)
                 + qa.check_parametric(par) + qa.check_counterfactual(cf))
        if par.get("warnings"):
            flags.append({"severity": "WARNING", "check": "parametric-orphan", "field": "insurance",
                          "issue": ";".join(par["warnings"]), "suggested_fix": "map to register"})
        qc = qa.summarize(flags)
        fc = {"forecast_id": inp.regional.forecast_id,
              "generated_at": datetime.now(ist).isoformat(),
              "prompt_version": "MASTER-FORECASTER-1.1.0",
              "gee_tile": {"source": tile.get("source", "stub"), "date": tile.get("date_acquired", tile.get("date")),
                           "cached": tile.get("cached", False), "thumb_url": tile.get("thumb_url")},
              "hazard_narrative": narrative, "vulnerability_register": reg,
              "cascade_impact": casc, "advisories": advs,
              "parametric": par, "counterfactual": cf,
              "data_conflicts": conflicts, "quality_check": qc}
        Path(a.out).write_text(json.dumps(fc, indent=2))
        h = hashlib.md5(json.dumps(fc, sort_keys=True).encode()).hexdigest()[:8]
        log("info", "cli", "DONE", f"forecast {inp.regional.forecast_id} hash={h} status={qc['overall_status']}", {})
        return config.EXIT_PASS if qc["overall_status"] != "block" else config.EXIT_QA_BLOCK
    except StageError as e:
        log("error", "stage", "STAGE_INVARIANT", str(e), {})
        write_error(a.artifacts, "stage", e, a.verbose)
        return config.EXIT_STAGE_INVARIANT
    except Exception as e:
        log("error", "internal", "INTERNAL", str(e), {})
        write_error(a.artifacts, "internal", e, a.verbose)
        return config.EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
