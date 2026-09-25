"""MASTER-FORECASTER-1.1.0 Sec 1 constants. Single source of truth."""

BUFFER_M = 50
TRIGGER_SCORE = 70
MAX_HOPS = 3
DEFAULT_CRS = "EPSG:32645"

CHAR_LIMITS = {"sms": 280, "email": 500}
CHANNEL_DEFAULT = "sms"

FRAGILITY = {
    "substation": {"inundation_m": 0.5},
    "transmission_tower": {"wind_kmh": 150, "inundation_m": 1.5},
    "arterial_road": {"inundation_m": 0.3},
    "hospital": {"inundation_m": 1.0, "inundation_m_with_backup": 1.5},
    "cyclone_shelter": {"wind_kmh": 200},
    "water_plant": {"inundation_m": 0.8},
    "telecom_tower": {"wind_kmh": 180},
}

PAYOUT_TABLE = {(150, 1.5): 0.40, (180, 2.0): 0.70, (200, 3.0): 1.00}

COUNTERFACTUAL_HORIZONS_H = [0, 6, 12, 24]

GEE_CACHE_DIR = ".cache/gee"
SLOSH_LOOKUP_PATH = "data/slosh_lookup.npz"
SURGE_INTERP_METHOD = "bilinear"
RAIN_THRESHOLD_MM_24H = 150
SOIL_SATURATION_WEIGHT = 0.3
SLOPE_WEIGHT = 0.2

EXIT_PASS = 0
EXIT_QA_BLOCK = 1
EXIT_LOADER_FAIL = 2
EXIT_STAGE_INVARIANT = 3
EXIT_INTERNAL = 4
EXIT_GEE_NO_CACHE = 5
