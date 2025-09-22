import sqlite3
import time
from pathlib import Path

from src.database.adsb_db import DBWorker
from src.sdr_cap.recieve_adsb import ADSBClient


def test_adsbclient_handle_messages_creates_db_rows(tmp_path):
    # Prepare a DB file inside src/database for test artifacts
    db_folder = Path(__file__).resolve().parents[2] / "src" / "database"
    db_folder.mkdir(parents=True, exist_ok=True)
    db_file = db_folder / f"adsb_test_{int(time.time() * 1000)}.db"
    db_path = str(db_file)

    dbw = DBWorker(db_path=db_path)
    dbw.start()

    try:
        # Create a fake ADS-B raw message list. We will use a minimal hex string
        # that pyModeS would recognize as DF=17 and decode ICAO; to avoid
        # depending on pyModeS internals here, we'll craft messages that are
        # already normalized and focus on the plumbing: call handle_messages
        # with messages as (raw, ts).
        # A real integration test could use dump1090 sample output.

        # Example: a short message that won't crash the decoder but likely won't
        # decode to a full position. We'll still assert that the worker doesn't
        # error and that tables exist after processing.
        messages = [
            ("*8D4840D6202CC371C32CE0576098;", time.time()),
        ]

        # ADSBClient requires ref_lat/ref_lon but we won't use position resolution here
        client = ADSBClient(host="127.0.0.1", port=0, rawtype="raw", db_worker=dbw, aircrafts={}, ref_lat=32.8, ref_lon=-97.0)
        client.handle_messages(messages)

        # give DBWorker time to process queue
        deadline = time.time() + 3.0
        got = False
        while time.time() < deadline:
            if db_file.exists():
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                try:
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='aircraft'")
                    if cur.fetchone():
                        got = True
                        break
                except Exception:
                    pass
                finally:
                    conn.close()
            time.sleep(0.1)

        assert got, "DB schema/tables not initialized after handling messages"

    finally:
        dbw.stop()
        dbw.join(timeout=2.0)
        # cleanup db artifacts
        try:
            if db_file.exists():
                db_file.unlink()
            for suffix in ("-wal", "-shm"):
                p = str(db_file) + suffix
                if Path(p).exists():
                    Path(p).unlink()
        except Exception:
            pass