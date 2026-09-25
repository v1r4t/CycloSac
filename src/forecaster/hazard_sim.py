"""Hazard sim stubs: Holland wind + SLOSH bilinear placeholder."""
import math


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
