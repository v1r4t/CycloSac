"""Loader: strict validate 10 inputs, fail-fast exit 2."""
import json
from pathlib import Path
from pydantic import ValidationError
from . import config
from .models import ForecastInput, Asset, Met, Ward, Dependency, Regional


class LoaderError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.code = config.EXIT_LOADER_FAIL
        self.errors = errors or []


REQUIRED = ["aoi.geojson", "surge.geojson", "rainfall.geojson", "wind.geojson",
            "met.json", "assets.json", "population.json", "dependencies.json",
            "audience.json", "regional.json", "insurance.json"]


def _json(p: Path):
    return json.loads(p.read_text())


def load_inputs(inputs_dir: str) -> ForecastInput:
    d = Path(inputs_dir)
    missing = [f for f in REQUIRED if not (d / f).exists() and f != "insurance.json"]
    if missing:
        raise LoaderError(f"missing inputs: {missing}")
    try:
        assets = [Asset(**a) for a in _json(d / "assets.json")]
        met = Met(**_json(d / "met.json"))
        wards = [Ward(**w) for w in _json(d / "population.json")]
        deps = [Dependency(**x) for x in _json(d / "dependencies.json")]
        audience = _json(d / "audience.json")
        regional = Regional(**_json(d / "regional.json"))
        ins = _json(d / "insurance.json") if (d / "insurance.json").exists() else []
        raw = {f: _json(d / f) for f in ["surge.geojson", "rainfall.geojson", "wind.geojson", "aoi.geojson"]}
    except ValidationError as e:
        raise LoaderError(f"validation failed: {e.errors()}", e.errors())
    # consistency: dependency endpoints must exist
    ids = {a.asset_id for a in assets}
    for x in deps:
        if x.from_asset not in ids or x.to_asset not in ids:
            raise LoaderError(f"dependency references unknown asset: {x}")
    return ForecastInput(assets=assets, met=met, wards=wards, dependencies=deps,
                         audience=audience, regional=regional, insurance=ins, raw=raw)
