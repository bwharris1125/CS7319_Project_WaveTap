CREATE TABLE IF NOT EXISTS aircraft (
    icao TEXT PRIMARY KEY,
    callsign TEXT,
    first_seen REAL,
    last_seen REAL
);

CREATE TABLE IF NOT EXISTS flight_session (
    id TEXT PRIMARY KEY,          -- uuid string
    aircraft_icao TEXT,
    start_time REAL,
    end_time   REAL,
    FOREIGN KEY (aircraft_icao) REFERENCES aircraft(icao)
);

CREATE INDEX IF NOT EXISTS idx_flight_session_aircraft ON flight_session(aircraft_icao);

CREATE TABLE IF NOT EXISTS path (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    icao TEXT,
    ts REAL,           -- epoch seconds
    ts_iso TEXT,       -- ISO8601 UTC snapshot for easy human reads
    lat REAL,
    lon REAL,
    alt REAL,
    FOREIGN KEY (session_id) REFERENCES flight_session(id),
    FOREIGN KEY (icao) REFERENCES aircraft(icao)
);

CREATE INDEX IF NOT EXISTS idx_path_icao_ts ON path(icao, ts);
