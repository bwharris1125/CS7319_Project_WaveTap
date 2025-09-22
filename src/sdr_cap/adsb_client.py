import logging

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient


class ADSBClient(TcpClient):
    def __init__(self, host, port, data_type):
        logging.info(f"Starting ADSBClient to {host}:{port} type={data_type}")
        super(ADSBClient, self).__init__(host, port, data_type)
        self.aircraft_data = {}

    def handle_messages(self, messages):
        for msg, timestamp in messages:
            if len(msg) != 28:
                continue
            df = pms.df(msg)
            if pms.crc(msg) == 1:
                continue
            if df == 17:
                tc = pms.typecode(msg)
                icao = pms.icao(msg)
                if tc is None or icao is None:
                    continue
                # Initialize aircraft entry if not present
                if icao not in self.aircraft_data:
                    self.aircraft_data[icao] = {
                        "icao": icao,
                        "callsign": None,
                        "position": None,
                        "velocity": None,
                        "altitude": None,
                        "last_update": None,
                    }
                entry = self.aircraft_data[icao]
                entry["last_update"] = timestamp
                if 1 <= tc <= 4:
                    entry["callsign"] = pms.adsb.callsign(msg)
                if 5 <= tc <= 8:
                    msgbin = pms.common.hex2bin(msg)
                    cprlat = pms.common.bin2int(msgbin[54:71]) / 131072.0
                    cprlon = pms.common.bin2int(msgbin[71:88]) / 131072.0
                    entry["position"] = {"lat": cprlat, "lon": cprlon}
                    entry["velocity"] = pms.adsb.surface_velocity(msg)
                if 9 <= tc <= 18:
                    alt = pms.adsb.altitude(msg)
                    msgbin = pms.common.hex2bin(msg)
                    cprlat = pms.common.bin2int(msgbin[54:71]) / 131072.0
                    cprlon = pms.common.bin2int(msgbin[71:88]) / 131072.0
                    entry["altitude"] = alt
                    entry["position"] = {"lat": cprlat, "lon": cprlon}
                if tc == 19:
                    velocity = pms.adsb.velocity(msg)
                    if velocity is not None:
                        entry["velocity"] = {
                            "speed": velocity[0],
                            "track": velocity[1],
                            "vertical_rate": velocity[2],
                            "type": velocity[3],
                        }
                # Other typecodes can be added as needed
                logging.debug(f"Updated aircraft {icao}")


def run_client():
    host = "192.168.50.106"
    port = 30002

    client = ADSBClient(host, port, "raw")
    client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # # confirm library workign correctly
    # pms.tell("8D4840D6202CC371C32CE0576098")

    run_client()
