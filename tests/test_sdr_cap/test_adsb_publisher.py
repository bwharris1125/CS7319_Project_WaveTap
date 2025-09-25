import asyncio
import json

import pytest
import websockets

from sdr_cap.adsb_publisher import ADSBPublisher

HOST = "127.0.0.1"
SRC_PORT = 30002
DEST_PORT = 8443

@pytest.mark.asyncio
async def test_adsb_publisher_receives(monkeypatch):
    # Mock ADSBClient to provide predictable data
    class MockClient:
        aircraft_data = {"TEST123": {"callsign": "TEST", "altitude": 10000, "position": {"lat": 51.0, "lon": -0.1}}}
        def run(self):
            pass

    # Patch ADSBPublisher to use MockClient
    monkeypatch.setattr("sdr_cap.adsb_publisher.ADSBClient", lambda host, port, dtype: MockClient())
    publisher = ADSBPublisher(HOST, SRC_PORT, HOST, DEST_PORT, interval=1)

    async def run_publisher():
        await publisher.run()

    # Start publisher in background
    task = asyncio.create_task(run_publisher())
    await asyncio.sleep(0.5)  # Give server time to start

    # Connect as a websocket client
    uri = f"ws://{HOST}:{DEST_PORT}"
    async with websockets.connect(uri) as ws:
        data = await ws.recv()
        decoded = json.loads(data)
        assert "TEST123" in decoded
        assert decoded["TEST123"]["callsign"] == "TEST"
        assert decoded["TEST123"]["altitude"] == 10000
        assert decoded["TEST123"]["position"]["lat"] == 51.0
        assert decoded["TEST123"]["position"]["lon"] == -0.1

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
