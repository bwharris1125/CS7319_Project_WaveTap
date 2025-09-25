import os
import sqlite3
import time
import uuid
from pathlib import Path

from database.adsb_db import AircraftState, DBWorker


def test_aircraftstate_defaults():
    a = AircraftState(icao="ABCDEF")
    assert a.icao == "ABCDEF"
    assert a.callsign is None
    assert a.session_id is None
    assert isinstance(a.last_seen, float)
    # last_seen should be recent (within last 5 seconds)
    assert time.time() - a.last_seen < 5


def test_dbworker_processes_tasks(tmp_path):
    # place temporary sqlite file inside the project src/database folder so it
    # lives alongside other DB artifacts during test runs
    db_folder = Path(__file__).resolve().parents[2] / "src" / "database"
    db_folder.mkdir(parents=True, exist_ok=True)
    db_file = db_folder / f"test_adsb_{int(time.time() * 1000)}.db"
    db_path = str(db_file)

    worker = DBWorker(db_path=db_path)
    worker.start()

    try:
        # enqueue an upsert for an aircraft
        icao = "ABC123"
        callsign = "TEST123"
        ts = time.time()
        worker.enqueue(("upsert_aircraft", icao, callsign, ts, ts))

        # create a session and add a path point
        session_id = str(uuid.uuid4())
        worker.enqueue(("start_session", session_id, icao, ts))
        iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
        worker.enqueue(("insert_path", session_id, icao, ts, iso, 32.0, -96.0, 1000.0))
        worker.enqueue(("end_session", session_id, ts + 10.0))

        # wait for DB to be populated (timeout after ~5s)
        deadline = time.time() + 5.0
        rows_found = False
        while time.time() < deadline:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                try:
                    cur.execute("SELECT count(*) FROM path")
                    cnt = cur.fetchone()[0]
                    if cnt >= 1:
                        rows_found = True
                        break
                except sqlite3.OperationalError:
                    # table may not be initialized yet
                    pass
                finally:
                    conn.close()
            time.sleep(0.1)

        assert rows_found, "DBWorker did not insert path row in time"

        # verify aircraft row exists
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT icao, callsign FROM aircraft WHERE icao = ?", (icao,))
        row = cur.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == icao
        assert row[1] == callsign

    finally:
        # stop worker and join
        worker.stop()
        worker.join(timeout=3.0)
        # cleanup file and WAL/SHM artifacts
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
            for suffix in ("-wal", "-shm"):
                p = db_path + suffix
                if os.path.exists(p):
                    os.remove(p)
        except Exception:
            pass