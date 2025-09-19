"""IQ Stream Client - Receives and processes IQ data from the streaming server."""

import socket
import struct
import time
from typing import Optional

import numpy as np

from utilities.wave_tap_logger import get_wt_logger


class IQStreamClient:
    """
    Client for receiving IQ data from the SDR streaming server.

    Connects to the IQ stream server and processes received samples
    for analysis, decoding, or visualization.
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.logger = self._setup_logging()

    def _setup_logging(self):
        return get_wt_logger("IQStreamClient")

    def connect(self) -> bool:
        """Connect to the IQ stream server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable TCP keepalive
            try:
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1
                )
            except Exception:
                pass
            # small recv timeout to detect dead peers faster
            self.socket.settimeout(10.0)
            self.socket.connect((self.host, self.port))
            self.logger.info(
                f"Connected to IQ stream server at {self.host}:{self.port}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            return False

    def receive_samples(self) -> Optional[np.ndarray]:
        """
        Receive a batch of IQ samples from the server.

        Returns:
            Complex numpy array of IQ samples, or None if error/disconnection
        """
        if not self.socket:
            return None

        try:
            # Read header (4-byte sample count)
            header_data = self._receive_exact(4)
            if not header_data:
                return None

            sample_count = struct.unpack(">I", header_data)[0]

            # Read IQ data (sample_count * 2 floats * 4 bytes each)
            data_size = sample_count * 2 * 4  # I,Q pairs as float32
            iq_data = self._receive_exact(data_size)
            if not iq_data:
                self.logger.debug(
                    "No IQ data received; connection may be closed"
                )
                return None

            # Convert bytes to numpy array and reshape to complex samples
            floats = np.frombuffer(iq_data, dtype=np.float32)
            complex_samples = floats[0::2] + 1j * floats[1::2]

            return complex_samples

        except Exception as e:
            self.logger.error(f"Error receiving samples: {e}")
            return None

    def _receive_exact(self, size: int) -> Optional[bytes]:
        """Receive exact number of bytes from socket."""
        data = b""
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                return None  # Connection closed
            data += chunk
        return data

    def process_samples(self, samples: np.ndarray):
        """
        Process received IQ samples.

        Override this method in subclasses for specific processing:
        - ADS-B decoding
        - FM demodulation
        - Spectrum analysis
        - Signal detection
        """
        # Example: Calculate power spectrum
        fft = np.fft.fft(samples)
        power_spectrum = np.abs(fft) ** 2

        # Example: Find peak frequency
        peak_idx = np.argmax(power_spectrum)
        sample_rate = 2.048e6  # Should match server config
        freq_bins = np.fft.fftfreq(len(samples), 1 / sample_rate)
        peak_freq = freq_bins[peak_idx]

        self.logger.info(
            f"Received {len(samples)} samples, peak at {peak_freq / 1e6:.3f} MHz"
        )

    def start_receiving(self, max_samples: Optional[int] = None):
        """
        Start receiving and processing IQ samples.

        Args:
            max_samples: Maximum number of sample batches to process (None for infinite)
        """
        # Attempt to connect with exponential backoff if connection drops
        backoff = 1.0
        self.running = True
        sample_count = 0

        try:
            while self.running and (
                max_samples is None or sample_count < max_samples
            ):
                if not self.socket:
                    connected = self.connect()
                    self.logger.debug(f"Connection status: {connected}")
                    if not connected:
                        self.logger.warning(
                            f"Connect failed, retrying in {backoff}s"
                        )
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 30.0)
                        continue
                    # reset backoff on successful connect
                    backoff = 1.0

                samples = self.receive_samples()
                if samples is None:
                    # connection likely closed; disconnect and attempt reconnect
                    self.logger.warning(
                        "No samples received; connection closed. Reconnecting..."
                    )
                    self.disconnect()
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)
                    continue

                # Process and continue
                try:
                    self.process_samples(samples)
                except Exception as e:
                    self.logger.error(f"Error processing samples: {e}")

                sample_count += 1

        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Stopping client.")
        except Exception as e:
            self.logger.error(f"Error in receive loop: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        """Disconnect from the server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
                pass
            self.socket = None
        self.logger.info("Disconnected from server.")


def main():
    """Usage of the IQ stream client."""
    client = IQStreamClient("localhost", 8080)
    print("Starting basic IQ stream client...")
    print("Press Ctrl+C to stop.")

    try:
        client.start_receiving(max_samples=None)
    except KeyboardInterrupt:
        print("Client stopped.")


if __name__ == "__main__":
    main()
