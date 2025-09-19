from database.adsb_db import AircraftDB
from src.utilities.aircraft_data import AircraftData


def test_db_insert_and_get():
    db = AircraftDB(path=":memory:")
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
    row_id = db.insert(a)
    assert isinstance(row_id, int) and row_id > 0
    got = db.get(row_id)
    assert got is not None
    assert got.icao == a.icao
    assert got.callsign == a.callsign
    assert got.latitude == a.latitude
    assert got.longitude == a.longitude
    db.close()
