import sqlite3
from typing import List, Optional

from src.utilities.aircraft_data import AircraftData

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS aircraft_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    icao TEXT,
    callsign TEXT,
    latitude REAL,
    longitude REAL,
    altitude_m REAL,
    heading_deg REAL,
    groundspeed_m_s REAL,
    vertical_rate_m_s REAL,
    squawk TEXT,
    emergency INTEGER,
    timestamp REAL,
    raw TEXT
);
"""


class AircraftDB:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.executescript(DB_SCHEMA)
        self.conn.commit()

    def insert(self, a: AircraftData) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO aircraft_events
            (icao, callsign, latitude, longitude, altitude_m, heading_deg, groundspeed_m_s, vertical_rate_m_s, squawk, emergency, timestamp, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                a.icao,
                a.callsign,
                a.latitude,
                a.longitude,
                a.altitude_m,
                a.heading_deg,
                a.groundspeed_m_s,
                a.vertical_rate_m_s,
                a.squawk,
                1 if a.emergency else 0 if a.emergency is not None else None,
                a.timestamp,
                str(a.raw),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, row_id: int) -> Optional[AircraftData]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM aircraft_events WHERE id = ?", (row_id,))
        row = cur.fetchone()
        if not row:
            return None
        # map by column index
        _, icao, callsign, lat, lon, alt_m, heading, gs, vr, squawk, emergency, timestamp, raw = row
        return AircraftData(
            icao=icao,
            callsign=callsign,
            latitude=lat,
            longitude=lon,
            altitude_m=alt_m,
            heading_deg=heading,
            groundspeed_m_s=gs,
            vertical_rate_m_s=vr,
            squawk=squawk,
            emergency=bool(emergency) if emergency is not None else None,
            timestamp=timestamp,
            raw={},
        )

    def list_recent(self, limit: int = 100) -> List[AircraftData]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM aircraft_events ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        results = []
        for row in rows:
            _, icao, callsign, lat, lon, alt_m, heading, gs, vr, squawk, emergency, timestamp, raw = row
            results.append(
                AircraftData(
                    icao=icao,
                    callsign=callsign,
                    latitude=lat,
                    longitude=lon,
                    altitude_m=alt_m,
                    heading_deg=heading,
                    groundspeed_m_s=gs,
                    vertical_rate_m_s=vr,
                    squawk=squawk,
                    emergency=bool(emergency) if emergency is not None else None,
                    timestamp=timestamp,
                    raw={},
                )
            )
        return results

    def close(self):
        self.conn.close()
