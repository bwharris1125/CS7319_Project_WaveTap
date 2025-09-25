import asyncio
import json
import logging
import threading

import websockets

from sdr_cap.adsb_client import ADSBClient

# TODO: have this publish to a message queue instead of printing
# - Determine if this needs to be its own file/class or can be a function


class ADSBPublisher:
    def __init__(self, host, src_port=30002, dest_ip="0.0.0.0", dest_port=8443, interval=3):
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.interval = interval
        self.src_client = ADSBClient(host, src_port, "raw")
        self.clients = set()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def publish_data(self):
        while True:
            if self.clients:
                data = json.dumps(self.src_client.aircraft_data, default=str)
                await asyncio.gather(*[ws.send(data) for ws in self.clients])
            await asyncio.sleep(self.interval)

    async def run(self):
        logging.info("Starting ADSBPublisher...")
        # logging.debug(f"WebSocket server on {self.dest_ip}:{self.dest_port}")
        # Start ADSB client in a thread
        threading.Thread(target=self.src_client.run, daemon=True).start()
        # Start WebSocket server
        async with websockets.serve(self.handler, self.dest_ip, self.dest_port):
            await self.publish_data()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    publisher = ADSBPublisher(host="192.168.50.106")
    asyncio.run(publisher.run())