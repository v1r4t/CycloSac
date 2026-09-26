"""Build synthetic SLOSH lookup grid (documented stub).

Provenance: placeholder geometry for the demo. Formula mirrors
hazard_sim.surge_depth so lookup ~= analytic stub. Replace with NOAA
SLOSH basin grids (NOAA NWS 48) for production; see docs/GEE.md.
Grid axes: intensity_kmh 100..220 step 5, pressure_hpa 940..1010 step 5,
dist_km 0..60 step 5. Value: surge_depth formula output.
"""
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from forecaster.hazard_sim import surge_depth

INT = np.arange(100, 221, 5)
PRS = np.arange(940, 1011, 5)
DST = np.arange(0, 61, 5)


def build(path) -> str:
    from pathlib import Path as _P
    path = str(path)
    _P(path).parent.mkdir(parents=True, exist_ok=True)
    g = np.zeros((len(INT), len(PRS), len(DST)))
    for i, v in enumerate(INT):
        for j, p in enumerate(PRS):
            for k, d in enumerate(DST):
                g[i, j, k] = surge_depth(float(v), float(p), float(d))
    np.savez(path, grid=g, intensity=INT, pressure=PRS, dist=DST,
             provenance="synthetic stub mirroring surge_depth; replace with NOAA SLOSH")
    return path


if __name__ == "__main__":
    import sys as _s
    print(build(_s.argv[1] if len(_s.argv) > 1 else "data/slosh_lookup.npz"))
