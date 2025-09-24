import logging
import sys
import threading
import time

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


def print_aircraft_data(client, interval=3):
    last_lines = 0
    while True:
        # Table header
        header = f"{'ICAO':<8} {'CALLSIGN':<10} {'LAT':>10} {'LON':>10} {'ALT':>8}"
        output_lines = [header]
        # Table rows
        for icao, entry in client.aircraft_data.items():
            callsign = str(entry.get("callsign", ""))
            position = entry.get("position", {})
            altitude = str(entry.get("altitude", ""))
            lat = f"{position.get('lat', ''):.5f}" if position and position.get("lat") is not None else ""
            lon = f"{position.get('lon', ''):.5f}" if position and position.get("lon") is not None else ""
            output_lines.append(f"{icao:<8} {callsign:<10} {lat:>10} {lon:>10} {altitude:>8}")
        # Move cursor up to overwrite previous output
        if last_lines:
            sys.stdout.write(f"\033[{last_lines}F")
        # Write all lines, each followed by a single newline
        for line in output_lines:
            sys.stdout.write(line + "\n")
        # If fewer lines than last time, clear remaining
        extra_lines = last_lines - len(output_lines)
        if extra_lines > 0:
            sys.stdout.write((' ' * 80 + '\n') * extra_lines)
        sys.stdout.flush()
        last_lines = len(output_lines)
        time.sleep(interval)


def run_client():
    host = "192.168.50.106"
    port = 30002

    client = ADSBClient(host, port, "raw")
    t = threading.Thread(target=print_aircraft_data, args=(client,))
    t.daemon = True
    t.start()
    client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # # confirm library workign correctly
    # pms.tell("8D4840D6202CC371C32CE0576098")

    run_client()
