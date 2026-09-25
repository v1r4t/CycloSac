"""Task 1 RED: config constants per MASTER-FORECASTER-1.1.0 Sec 1."""
from forecaster import config


def test_buffer_m():
    assert config.BUFFER_M == 50


def test_trigger_score():
    assert config.TRIGGER_SCORE == 70


def test_max_hops():
    assert config.MAX_HOPS == 3


def test_default_crs():
    assert config.DEFAULT_CRS == "EPSG:32645"


def test_char_limits():
    assert config.CHAR_LIMITS["sms"] == 280
    assert config.CHAR_LIMITS["email"] == 500


def test_payout_table():
    assert config.PAYOUT_TABLE[(150, 1.5)] == 0.40
    assert config.PAYOUT_TABLE[(180, 2.0)] == 0.70
    assert config.PAYOUT_TABLE[(200, 3.0)] == 1.00


def test_counterfactual_horizons():
    assert config.COUNTERFACTUAL_HORIZONS_H == [0, 6, 12, 24]


def test_exit_codes():
    assert config.EXIT_PASS == 0
    assert config.EXIT_QA_BLOCK == 1
    assert config.EXIT_LOADER_FAIL == 2
    assert config.EXIT_STAGE_INVARIANT == 3
    assert config.EXIT_INTERNAL == 4
    assert config.EXIT_GEE_NO_CACHE == 5
