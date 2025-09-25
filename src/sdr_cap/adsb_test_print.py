import logging
import sys
import threading
import time

from adsb_publisher import ADSBClient


# TODO: should this be part of the class?
def print_aircraft_data(client, interval: int = 3) -> None:
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


def run_client() -> None:
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
