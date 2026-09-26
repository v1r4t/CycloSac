"""Hazard sim: Holland wind + SLOSH lookup (npz) with analytic fallback."""
import math

try:
    import numpy as _np
except ImportError:
    _np = None


def holland_wind(intensity_kmh: float, radius_km: float) -> float:
    # prototype parametric decay: V(r) = Vmax * exp(-r/100)
    return round(max(0.0, intensity_kmh * math.exp(-radius_km / 100)), 1)


def surge_depth(intensity_kmh: float, pressure_hpa: float, dist_km: float) -> float:
    # placeholder bilinear on SLOSH lookup: scale by intensity + pressure deficit
    base = max(0.0, (1010 - pressure_hpa) / 50) * (intensity_kmh / 150)
    depth = base * math.exp(-dist_km / 30)
    return round(min(15.0, depth), 2)


def damage_index(rain_mm: float, soil_sat: float, slope: float) -> float:
    return round(min(1.0, rain_mm / 300 * 0.5 + soil_sat * 0.3 + slope * 0.2), 3)


def load_lookup(path):
    """Load npz SLOSH grid or return None (analytic fallback)."""
    if _np is None:
        return None
    try:
        z = _np.load(path)
        return {"grid": z["grid"], "intensity": z["intensity"],
                "pressure": z["pressure"], "dist": z["dist"]}
    except Exception:
        return None


def _nearest_idx(arr, v):
    return int(abs(arr - v).argmin())


def surge_from_lookup(grid, intensity_kmh: float, pressure_hpa: float, dist_km: float) -> float:
    """Nearest-grid lookup (grid mirrors surge_depth; see scripts/make_slosh_lookup.py)."""
    g = grid["grid"]
    i = _nearest_idx(grid["intensity"], intensity_kmh)
    j = _nearest_idx(grid["pressure"], pressure_hpa)
    k = _nearest_idx(grid["dist"], dist_km)
    return round(float(g[i, j, k]), 2)
