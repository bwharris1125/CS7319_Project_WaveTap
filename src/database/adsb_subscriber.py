import asyncio
import json
import logging
import sys
import time

import websockets


class ADSBSubscriber:
    """
    ADSBSubscriber connects to a WebSocket publisher, receives ADS-B aircraft
    data, and maintains a rolling in-memory dictionary of aircraft data on the
    subscriber side.
    """
    def __init__(self, uri: str):
        """
        Initialize the subscriber with the WebSocket URI.
        """
        self.uri = uri
        self.aircraft_data = {}

    async def connect_and_listen(self):
        """
        Connect to the WebSocket publisher and update aircraft_data as new
        data arrives.
        # TODO HANDLE FAILED CONNECTIONS AND DISCONNECTIONS GRACEFULLY
        """
        async with websockets.connect(self.uri) as ws:
            logging.info(f"Connected to publisher at {self.uri}")
            while True:
                data = await ws.recv()
                try:
                    received = json.loads(data)
                    if isinstance(received, dict):
                        self.aircraft_data = received
                        logging.debug(f"Updated aircraft_data with {len(received)} entries.")
                except Exception as e:
                    logging.warning(f"Failed to decode message: {e}")

    # TODO write to database
    async def save_to_db(self):
        """
        Placeholder for saving aircraft_data to a database.
        """
        pass


def print_aircraft_data(collector, interval: int = 3) -> None:
    last_lines = 0
    while True:
        # Table header
        header = f"{'ICAO':<8} {'CALLSIGN':<10} {'LAT':>10} {'LON':>10} {'ALT':>8}"
        output_lines = [header]
        # Table rows
        for icao, entry in collector.aircraft_data.items():
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


async def main():
    uri = "ws://127.0.0.1:8443" # TODO make configurable
    subscriber = ADSBSubscriber(uri)
    await asyncio.gather(
        subscriber.connect_and_listen(),
        # print_aircraft_data(subscriber) # only needed for
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
