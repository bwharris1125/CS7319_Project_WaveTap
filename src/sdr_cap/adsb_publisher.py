import asyncio
import json
import logging
import threading

import pyModeS as pms
import websockets
from pyModeS.extra.tcpclient import TcpClient


class ADSBClient(TcpClient):
    """
    ADSBClient connects to a TCP source of ADS-B messages, decodes them,
    and maintains a rolling in-memory dictionary of aircraft data.
    """
    def __init__(self, host, port, data_type):
        super(ADSBClient, self).__init__(host, port, data_type)
        self.aircraft_data = {}
        logging.info(f"Starting ADSBClient on {host}:{port}[{data_type}]")

    def handle_messages(self, messages: list[tuple[str, float]]) -> None:
        """
        Parse a batch of ADS-B messages and update aircraft_data with decoded
        information. Stores to local dictionary in self.aircraft_data.
        """
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
                # NOTE: Other typecodes can be added as needed
                # logging.debug(f"Updated aircraft {icao}") # extremely verbose


class ADSBPublisher:
    """
    ADSBPublisher manages a WebSocket server that periodically publishes
    processed ADS-B aircraft data from an ADSBClient to all connected clients.
    Handles clean startup and shutdown for microservice integration.
    """
    def __init__(self, host, src_port=30002, dest_ip="0.0.0.0", dest_port=8443, interval=3):
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.interval = interval
        self.src_client = ADSBClient(host, src_port, "raw")
        self.clients = set()
        self._client_thread = None
        self._shutdown_event = threading.Event()
        logging.info("Starting ADSBPublisher...")

    async def handler(self, websocket) -> None:
        """
        Handle a new WebSocket client connection and remove it on disconnect.
        """
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def publish_data(self) -> None:
        """
        Periodically publish the current aircraft data to all connected
        WebSocket clients.
        """
        while True:
            if self.clients:
                data = json.dumps(self.src_client.aircraft_data, default=str)
                await asyncio.gather(*[ws.send(data) for ws in self.clients])
            await asyncio.sleep(self.interval)

    async def run(self) -> None:
        """
        Start the ADSB client in a thread and run the WebSocket server for
        publishing data.
        """
        # Start ADSB client in a thread
        self._client_thread = threading.Thread(target=self.src_client.run, daemon=True)
        self._client_thread.start()
        # Start WebSocket server
        async with websockets.serve(self.handler, self.dest_ip, self.dest_port):
            await self.publish_data()

    # NOTE: not currently captured by `ctrl+c` due to async structure
    async def close(self) -> None:
        """
        Cleanly shut down the publisher, closing all WebSocket clients and
        stopping the ADSB client thread.
        """
        logging.info("Shutting down ADSBPublisher...")
        # Signal shutdown to any loops/threads
        self._shutdown_event.set()
        # Close all websocket clients
        for ws in list(self.clients):
            await ws.close()
        # Optionally join the client thread if needed
        if self._client_thread and self._client_thread.is_alive():
            self._client_thread.join(timeout=2)


async def main():
    publisher = ADSBPublisher(host="192.168.50.106")
    try:
        await publisher.run()
    except KeyboardInterrupt:
        # FIXME needs additional infrastructure due to async
        logging.info("KeyboardInterrupt received, shutting down...")
        await publisher.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())