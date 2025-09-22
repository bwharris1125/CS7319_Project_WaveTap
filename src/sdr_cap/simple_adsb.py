import logging

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient

from database.adsb_db import AircraftState


class ADSBClient(TcpClient):
    def __init__(self, host, port, data_type):
        logging.info(f"Starting ADSBClient to {host}:{port} type={data_type}")
        super(ADSBClient, self).__init__(host, port, data_type)

    def handle_messages(self, messages):
        for msg, _ in messages:
            # logging.info(f"Raw message: [{msg}, {_}]")
            if len(msg) != 28 : # wrong length
                logging.debug(f"Skipping wrong length message: {msg}")
                continue

            df = pms.df(msg)

            if df != 17 : # not ADS-B
                logging.debug(f"Skipping non-ADS-B message: {msg}")
                continue
            if pms.crc(msg) == 1: # bad CRC
                logging.debug(f"Skipping bad CRC message: {msg}")
                continue

            icao = pms.adsb.icao(msg)
            tc = pms.adsb.typecode(msg)

            logging.debug(f"Recieved message from {icao}.\n"
                         f"  Type Code: {tc}\n"
                         f"  Raw Message: {msg}")

            # aircraft = AircraftState(icao=icao, callsign=callsign)
            # return aircraft

def run_client():
    host = "192.168.50.106"
    port = 30002

    client = ADSBClient(host, port, "raw")
    client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # # confirm library workign correctly
    # pms.tell("8D4840D6202CC371C32CE0576098")

    run_client()
