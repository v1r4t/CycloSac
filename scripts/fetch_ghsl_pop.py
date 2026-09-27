"""Fetch real ward populations: JRC GHSL-POP 100m via live GEE, zonal sums.

Why GHSL not WorldPop: WorldPop direct downloads 403/404/500 from this
network on 2026-09-27; GHSL P2023A GHS_POP is the same evidence class
(100m global settlement population) and our GEE project is verified live.
Honest vintage labeling throughout — nothing here is live headcounts.

Usage: python scripts/fetch_ghsl_pop.py sample_inputs_demo [--apply]
  --apply rewrites population.json pops (keeps vulnerability_index) and
          writes population_source.json provenance.
Without --apply it only prints the sums.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

GHSL_IMAGE = "JRC/GHSL/P2023A/GHS_POP/2020"
SOURCE_LABEL = "JRC GHSL P2023A GHS_POP 2020 (100m) via Google Earth Engine"


def fetch(wards_geojson: dict, project: str | None = None) -> dict:
    import ee
    ee.Initialize(project=project or os.environ.get("GEE_PROJECT", "cyclone-forecast-123456"))
    feats = [ee.Feature(f["geometry"], {"ward_code": f["properties"]["ward_code"]})
             for f in wards_geojson["features"]]
    pop = ee.Image(GHSL_IMAGE)
    # Sea/no-data pixels carry large negative codes in this epoch — mask to 0
    # (documented; W2 covers open Bay of Bengal water).
    pop = pop.where(pop.lt(0), 0)
    sums = pop.reduceRegions(collection=ee.FeatureCollection(feats),
                             reducer=ee.Reducer.sum(), scale=100)
    out = {}
    for f in sums.getInfo()["features"]:
        code = f["properties"]["ward_code"]
        out[code] = int(round(f["properties"].get("sum", 0)))
    return out


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    d = Path(argv[0] if argv else "sample_inputs_demo")
    wards = json.loads((d / "wards.geojson").read_text())
    sums = fetch(wards)
    print(json.dumps(sums, indent=1))
    if "--apply" in argv:
        pop = json.loads((d / "population.json").read_text())
        for w in pop:
            if w["ward_code"] in sums:
                w["population"] = sums[w["ward_code"]]
        (d / "population.json").write_text(json.dumps(pop, indent=1))
        (d / "population_source.json").write_text(json.dumps(
            {"source": SOURCE_LABEL, "vintage": "2020",
             "fetched": str(date.today()), "wards": sums}, indent=1))
        print("applied + provenance written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
