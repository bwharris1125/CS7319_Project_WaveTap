# ADS-B Database Module
import logging
import queue
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AircraftState:
    icao: str
    callsign: Optional[str] = None
    session_id: Optional[str] = None
    last_seen: float = field(default_factory=time.time)
    # no heavy storage here; DB holds full history


class DBWorker(threading.Thread):
    def __init__(self, db_path: str):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.q = queue.Queue()
        self.conn = None
        # use a different name to avoid shadowing Thread._stop()
        self._stop_event = threading.Event()
        self._poll_rate = 0.5

    def run(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()
        cur = self.conn.cursor()
        while not self._stop_event.is_set():
            try:
                task = self.q.get(timeout=self._poll_rate)
            except queue.Empty:
                continue
            try:
                self._handle(task, cur)
                self.conn.commit()
            except Exception as e:
                logging.exception("DB task failed: %s", e)
        # drain queue once on stop
        while True:
            try:
                task = self.q.get_nowait()
                try:
                    self._handle(task, cur)
                    self.conn.commit()
                except Exception:
                    logging.exception("DB draining failed")
            except queue.Empty:
                break
        self.conn.close()

    def stop(self):
        self._stop_event.set()

    def enqueue(self, task):
        self.q.put(task)

    def _init_schema(self):
        """
        Attempt to load the schema from a nearby SQL file so there's a single
        source of truth. If the file isn't present (packaging edge case), fall
        back to the embedded SQL.
        """
        schema_path = Path(__file__).parent / "adsb_db_schema.sql"
        if schema_path.exists():
            try:
                sql = schema_path.read_text(encoding="utf-8")
                self.conn.executescript(sql)
                return
            except Exception as e:
                logging.exception("Failed to read/execute schema file %s: %s", schema_path, e)

        # Fallback embedded schema
        s = """
        CREATE TABLE IF NOT EXISTS aircraft (
            icao TEXT PRIMARY KEY,
            callsign TEXT,
            first_seen REAL,
            last_seen REAL
        );
        CREATE TABLE IF NOT EXISTS flight_session (
            id TEXT PRIMARY KEY,
            aircraft_icao TEXT,
            start_time REAL,
            end_time REAL,
            FOREIGN KEY (aircraft_icao) REFERENCES aircraft(icao)
        );
        CREATE INDEX IF NOT EXISTS idx_flight_session_aircraft ON flight_session(aircraft_icao);
        CREATE TABLE IF NOT EXISTS path (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            icao TEXT,
            ts REAL,
            ts_iso TEXT,
            lat REAL,
            lon REAL,
            alt REAL,
            FOREIGN KEY (session_id) REFERENCES flight_session(id),
            FOREIGN KEY (icao) REFERENCES aircraft(icao)
        );
        CREATE INDEX IF NOT EXISTS idx_path_icao_ts ON path(icao, ts);
        """
        self.conn.executescript(s)

    def _handle(self, task, cur):
        typ = task[0]
        if typ == "upsert_aircraft":
            _, icao, callsign, first_seen, last_seen = task
            cur.execute(
                "INSERT INTO aircraft (icao, callsign, first_seen, last_seen) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(icao) DO UPDATE SET callsign=?, last_seen=?",
                (icao, callsign, first_seen, last_seen, callsign, last_seen)
            )
        elif typ == "start_session":
            _, session_id, icao, start_ts = task
            cur.execute(
                "INSERT OR IGNORE INTO flight_session (id, aircraft_icao, start_time) VALUES (?, ?, ?)",
                (session_id, icao, start_ts)
            )
        elif typ == "end_session":
            _, session_id, end_ts = task
            cur.execute(
                "UPDATE flight_session SET end_time=? WHERE id=?",
                (end_ts, session_id)
            )
        elif typ == "insert_path":
            _, session_id, icao, ts, ts_iso, lat, lon, alt = task
            cur.execute(
                "INSERT INTO path (session_id, icao, ts, ts_iso, lat, lon, alt) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, icao, ts, ts_iso, lat, lon, alt)
            )
        else:
            logging.warning("Unknown DB task: %s", task)