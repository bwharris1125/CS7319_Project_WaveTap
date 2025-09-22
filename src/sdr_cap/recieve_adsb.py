#!/usr/bin/env python3
"""
adsb_logger.py
- Connects to dump1090 raw TCP (host,port)
- Uses pyModeS to decode ADS-B messages
- Groups continuous receptions into flight sessions (uuid)
- Inserts each position report (waypoint) into SQLite
- Run with: python adsb_logger.py --host 192.168.50.106 --port 30002 --db ./adsb.db --ref-lat 32.8 --ref-lon -97.0
"""
import argparse
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient

from database.adsb_db import AircraftState, DBWorker

# ----- CONFIG -----
SESSION_TIMEOUT = 300          # seconds without updates => session end (default 5 minutes)
SESSION_CLEANUP_INTERVAL = 10  # how often to scan for stale sessions (s)

# ----- ADS-B client -----
class ADSBClient(TcpClient):
    def __init__(self, host, port, rawtype, db_worker: DBWorker, aircrafts: Dict[str, AircraftState], ref_lat: float, ref_lon: float, session_timeout: int = SESSION_TIMEOUT):
        super().__init__(host, port, rawtype)
        self.db_worker = db_worker
        self.aircrafts = aircrafts
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.session_timeout = session_timeout

    def _normalize_msg(self, raw: str) -> str:
        m = raw.strip()
        if m.startswith("*"):
            m = m[1:]
        if m.endswith(";"):
            m = m[:-1]
        # keep only hex chars
        return "".join(ch for ch in m if ch in "0123456789abcdefABCDEF")

    def handle_messages(self, messages):
        now = time.time()
        for msg_raw, ts in messages:
            msg = self._normalize_msg(msg_raw)
            if not msg:
                continue
            # only process DF=17 (ADS-B)
            try:
                if pms.df(msg) != 17:
                    continue
            except Exception:
                continue

            # optional CRC check (skip if pms raises)
            try:
                if pms.crc(msg) != 0:
                    continue
            except Exception:
                pass

            try:
                icao = pms.adsb.icao(msg)
            except Exception:
                continue
            if not icao:
                continue

            ac = self.aircrafts.get(icao)
            if not ac:
                ac = AircraftState(icao=icao)
                self.aircrafts[icao] = ac
                # record first_seen via DB upsert
                self.db_worker.enqueue(("upsert_aircraft", icao, None, now, now))

            ac.last_seen = now

            # Callsign (TC 1-4)
            try:
                tc = pms.adsb.typecode(msg)
            except Exception:
                tc = None

            if tc and 1 <= tc <= 4:
                callsign = pms.adsb.callsign(msg)
                if callsign:
                    ac.callsign = callsign.strip()
                    self.db_worker.enqueue(("upsert_aircraft", icao, ac.callsign, now, now))

            # Altitude-only messages (TC 5-8) could be read for alt
            try:
                if tc and 9 <= tc <= 18:     # position (CPR even/odd)
                    pos = pms.adsb.position_with_ref(msg, self.ref_lat, self.ref_lon)
                    if pos:
                        lat, lon = pos
                        try:
                            alt = pms.adsb.altitude(msg)
                        except Exception:
                            alt = None
                        # ensure session
                        if not ac.session_id:
                            ac.session_id = str(uuid.uuid4())
                            self.db_worker.enqueue(("start_session", ac.session_id, icao, now))
                        ts_iso = datetime.fromtimestamp(now, tz=timezone.utc).isoformat()
                        self.db_worker.enqueue(("insert_path", ac.session_id, icao, now, ts_iso, lat, lon, alt))
                # TODO determine if we want to log velocity messages too
                # elif tc and 19 <= tc <= 22:   # velocity
                #     vel = None
                #     try:
                #         vel = pms.adsb.velocity(msg)
                #     except Exception:
                #         vel = None
                #     # optionally log velocity into DB as separate table/extend path: omitted for brevity
            except Exception:
                logging.exception("Failed to process message %s", msg)

# ----- Session manager thread -----
class SessionManager(threading.Thread):
    def __init__(self, aircrafts: Dict[str, AircraftState], db_worker: DBWorker, session_timeout: int = SESSION_TIMEOUT, interval: int = SESSION_CLEANUP_INTERVAL):
        super().__init__(daemon=True)
        self.aircrafts = aircrafts
        self.db_worker = db_worker
        self.session_timeout = session_timeout
        self.interval = interval
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            now = time.time()
            for icao, ac in list(self.aircrafts.items()):
                if ac.session_id and (now - ac.last_seen) > self.session_timeout:
                    logging.info("Ending session %s for %s (idle %ds)", ac.session_id, icao, int(now - ac.last_seen))
                    self.db_worker.enqueue(("end_session", ac.session_id, now))
                    ac.session_id = None
                # optionally: remove aircraft from memory after long inactivity
                # if (now - ac.last_seen) > (self.session_timeout * 10): del self.aircrafts[icao]
            time.sleep(self.interval)

    def stop(self):
        self._stop.set()

# ----- Main & CLI -----
def main():
    parser = argparse.ArgumentParser(description="ADS-B logger (dump1090 -> sqlite via pyModeS)")
    parser.add_argument("--host", required=True, help="dump1090 host (e.g. 192.168.50.106)")
    parser.add_argument("--port", type=int, default=30002, help="dump1090 raw port (default 30002)")
    parser.add_argument("--db", default="./adsb.db", help="sqlite DB file")
    parser.add_argument("--ref-lat", type=float, required=True, help="receiver reference latitude (for CPR position resolving)")
    parser.add_argument("--ref-lon", type=float, required=True, help="receiver reference longitude")
    parser.add_argument("--session-timeout", type=int, default=SESSION_TIMEOUT, help="seconds without updates to close session")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    dbw = DBWorker(args.db)
    dbw.start()
    aircrafts: Dict[str, AircraftState] = {}
    session_manager = SessionManager(aircrafts, dbw, session_timeout=args.session_timeout)
    session_manager.start()

    client = ADSBClient(host=args.host, port=args.port, rawtype="raw", db_worker=dbw, aircrafts=aircrafts,
                        ref_lat=args.ref_lat, ref_lon=args.ref_lon, session_timeout=args.session_timeout)
    try:
        logging.info("Connecting to %s:%d ...", args.host, args.port)
        client.run()   # blocks until TcpClient ends
    except KeyboardInterrupt:
        logging.info("Shutting down (KeyboardInterrupt)")
    finally:
        logging.info("Stopping session manager and DB worker...")
        session_manager.stop()
        dbw.stop()
        session_manager.join(timeout=2.0)
        dbw.join(timeout=2.0)
        logging.info("Stopped.")

if __name__ == "__main__":
    main()
