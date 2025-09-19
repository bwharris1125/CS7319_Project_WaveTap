import pytest

from src.utilities.aircraft_data import AircraftData


def test_from_adsb_dict_basic():
    sample = {
        "icao24": "abc123",
        "callsign": "TEST123",
        "lat": 32.0,
        "lon": -96.0,
        "altitude_ft": 10000,
        "groundspeed_kts": 250,
        "vertical_rate_fpm": -600,
        "squawk": "7000",
        "timestamp": 1620000000,
    }

    a = AircraftData.from_adsb_dict(sample)
    assert a.icao == "abc123"
    assert a.callsign == "TEST123"
    assert pytest.approx(a.altitude_m, rel=1e-3) == 10000 * 0.3048
    assert pytest.approx(a.groundspeed_m_s, rel=1e-3) == 250 * 0.514444
    assert pytest.approx(a.vertical_rate_m_s, rel=1e-3) == (-600/60.0) * 0.3048
    assert a.squawk == "7000"
    assert a.timestamp == 1620000000
