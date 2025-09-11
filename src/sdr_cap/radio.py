"""SDR IQ Stream Server - Captures and broadcasts IQ data over network."""

import logging
import os
import signal
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from rtlsdr import RtlSdr


@dataclass
class SDRConfig:
    """Configuration for SDR parameters."""

    sample_rate: float = 2.048e6  # 2.048 MHz
    center_freq: float = 1.09e9  # 1090 MHz (ADS-B)
    gain: str | int = "auto"  # Auto gain or specific dB value
    device_index: int = 0  # RTL-SDR device index
    buffer_size: int = 262144  # Buffer size for IQ samples

    @classmethod
    def from_env(cls) -> "SDRConfig":
        """Create SDRConfig from environment variables."""
        return cls(
            sample_rate=float(os.getenv("SDR_SAMPLE_RATE", 2.048e6)),
            center_freq=float(os.getenv("SDR_CENTER_FREQ", 1.09e9)),
            gain=os.getenv("SDR_GAIN", "auto"),
            device_index=int(os.getenv("SDR_DEVICE_INDEX", 0)),
            buffer_size=int(os.getenv("SDR_BUFFER_SIZE", 262144)),
        )


@dataclass
class NetworkConfig:
    """Configuration for network streaming."""

    host: str = "0.0.0.0"  # Bind to all interfaces
    port: int = 8080  # TCP port for IQ stream
    max_clients: int = 5  # Max concurrent client connections
    chunk_size: int = 8192  # Bytes per network chunk

    @classmethod
    def from_env(cls) -> "NetworkConfig":
        """Create NetworkConfig from environment variables."""
        return cls(
            host=os.getenv("NETWORK_HOST", "0.0.0.0"),
            port=int(os.getenv("NETWORK_PORT", 8080)),
            max_clients=int(os.getenv("NETWORK_MAX_CLIENTS", 5)),
            chunk_size=int(os.getenv("NETWORK_CHUNK_SIZE", 8192)),
        )


class IQStreamServer:
    """
    Captures IQ data from RTL-SDR and broadcasts it to multiple TCP clients.
    Supports real-time streaming with configurable parameters.
    """

    def __init__(self, sdr_config: SDRConfig, network_config: NetworkConfig):
        self.sdr_config = sdr_config
        self.network_config = network_config
        self.sdr = None
        self.server_socket: Optional[socket.socket] = None
        self.clients: list[socket.socket] = []
        self.running = False
        self.stats = {"samples_sent": 0, "clients_connected": 0, "errors": 0}
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the stream server."""
        logger = logging.getLogger("IQStreamServer")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def init_sdr(self) -> bool:
        """Initialize and configure the RTL-SDR device."""
        try:
            self.logger.info("Initializing RTL-SDR device...")
            self.sdr = RtlSdr(device_index=self.sdr_config.device_index)

            # Configure SDR parameters
            self.sdr.sample_rate = self.sdr_config.sample_rate
            self.sdr.center_freq = self.sdr_config.center_freq
            self.sdr.gain = self.sdr_config.gain

            self.logger.info("SDR Configured:")
            self.logger.info(
                f"  Sample Rate: {self.sdr.sample_rate / 1e6:.3f} MHz"
            )
            self.logger.info(
                f"  Center Freq: {self.sdr.center_freq / 1e6:.3f} MHz"
            )
            self.logger.info(f"  Gain: {self.sdr.gain}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize SDR: {e}")
            return False

    def start_tcp_server(self) -> bool:
        """Start TCP server for client connections."""
        try:
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.server_socket.bind(
                (self.network_config.host, self.network_config.port)
            )
            self.server_socket.listen(self.network_config.max_clients)
            self.server_socket.settimeout(1.0)  # Non-blocking accept

            self.logger.info(
                f"TCP server listening on {self.network_config.host}:{self.network_config.port}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
            return False

    def accept_clients(self):
        """Accept new client connections (runs in separate thread)."""
        while self.running:
            try:
                if self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    self.logger.info(f"Client connected from {addr}")
                    self.clients.append(client_socket)
                    self.stats["clients_connected"] += 1

            except socket.timeout:
                continue  # Timeout allows clean shutdown
            except Exception as e:
                if (
                    self.running
                ):  # Only log if we're still supposed to be running
                    self.logger.error(f"Error accepting clients: {e}")

    def broadcast_iq_data(self, samples: np.ndarray):
        """Broadcast IQ samples to all connected clients."""
        if not self.clients:
            return

        # Convert complex samples to bytes (I,Q pairs as float32)
        # Format: [I1, Q1, I2, Q2, ...]
        iq_data = (
            np.column_stack((samples.real, samples.imag))
            .flatten()
            .astype(np.float32)
        )
        data_bytes = iq_data.tobytes()

        # Send header with sample count
        header = struct.pack(">I", len(samples))  # Big-endian uint32

        disconnected_clients = []

        for client in self.clients:
            try:
                client.sendall(header + data_bytes)

            except (ConnectionResetError, BrokenPipeError):
                self.logger.info("Client disconnected")
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error sending to client: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients
        for client in disconnected_clients:
            try:
                client.close()
            except Exception:
                pass
            if client in self.clients:
                self.clients.remove(client)

    def iq_callback(self, samples: np.ndarray, context: Any):
        """Callback for SDR IQ samples."""
        try:
            self.broadcast_iq_data(samples)
            self.stats["samples_sent"] += len(samples)

        except Exception as e:
            self.logger.error(f"Error in IQ callback: {e}")
            self.stats["errors"] += 1

    def print_stats(self):
        """Print streaming statistics periodically."""
        while self.running:
            time.sleep(10)  # Print stats every 10 seconds
            if self.running:
                self.logger.info(
                    f"Stats - Samples: {self.stats['samples_sent']}, "
                    f"Clients: {len(self.clients)}, Errors: {self.stats['errors']}"
                )

    def _sdr_streaming_worker(self):
        """Worker thread for SDR async streaming."""
        try:
            self.logger.info("Starting IQ data capture...")
            self.sdr.read_samples_async(
                callback=self.iq_callback,
                num_samples=self.sdr_config.buffer_size,
                context=None,
            )
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")

    def start_streaming(self):
        """Start the IQ streaming server."""
        self.logger.info("Starting IQ Stream Server...")

        if not self.init_sdr():
            return False

        if not self.start_tcp_server():
            return False

        self.running = True

        # Start client acceptance & stats threads and stores reference
        self.client_thread = threading.Thread(
            target=self.accept_clients, daemon=True
        )
        self.client_thread.start()

        self.stats_thread = threading.Thread(
            target=self.print_stats, daemon=True
        )
        self.stats_thread.start()

        # Start SDR streaming in a dedicated thread
        self.sdr_thread = threading.Thread(
            target=self._sdr_streaming_worker, daemon=True
        )
        self.sdr_thread.start()

        return True

    def stop_streaming(self):
        """Stop the streaming server and cleanup resources."""
        self.logger.info("Stopping IQ Stream Server...")
        self.running = False

        # Stop SDR (cancel async read and close device)
        if self.sdr:
            try:
                self.sdr.cancel_read_async()
                # NOTE: "<LIBUSB_ERROR_INVALID_PARAM (-2)" expected here
                # TODO: Handle expected error
            except Exception as e:
                self.logger.error(
                    f"Failed to cancel SDR async read. Error: {e}"
                )

        # Join SDR thread for clean shutdown (with timeout)
        join_timeout = 5
        sdr_thread = getattr(self, "sdr_thread", None)
        if sdr_thread and sdr_thread.is_alive():
            self.logger.info(
                f"Waiting for sdr_thread to exit (timeout {join_timeout}s)..."
            )
            sdr_thread.join(timeout=join_timeout)
            if sdr_thread.is_alive():
                self.logger.error(
                    "sdr_thread did not exit in time. Forcing process exit to release SDR."
                )
                os._exit(0)

        # Now close SDR device
        if self.sdr:
            try:
                self.sdr.close()
                self.logger.info("SDR closed.")
            except Exception as e:
                self.logger.error(f"Failed to close SDR. Error: {e}")

        # Join other threads for clean shutdown (with timeout)
        for tname in ["client_thread", "stats_thread"]:
            t = getattr(self, tname, None)
            if t and t.is_alive():
                self.logger.info(
                    f"Waiting for {tname} to exit (timeout {join_timeout}s)..."
                )
                t.join(timeout=join_timeout)
                if t.is_alive():
                    self.logger.error(
                        f"{tname} did not exit in time. Forcing process exit to release SDR."
                    )
                    os._exit(0)

        # Close client connections
        for client in self.clients:
            try:
                client.close()
                self.logger.info("Client connection closed.")
            except Exception as e:
                self.logger.error(
                    f"Failed to close client connection. Error: {e}"
                )
        self.clients.clear()

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
                self.logger.info("Server socket closed.")
            except Exception as e:
                self.logger.error(f"Failed to close server socket. Error: {e}")

        self.logger.info("SDR Stream server stopped.")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global server_instance
    if server_instance:
        server_instance.logger.debug(
            f"Signal {signum} received, stopping server..."
        )
        server_instance.stop_streaming()


# Global server instance for signal handling
server_instance: Optional[IQStreamServer] = None


def main():
    """Main entry point for the IQ streaming server."""
    global server_instance

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create configurations
    sdr_config = SDRConfig(
        sample_rate=2.048e6,  # 2.048 MHz
        # center_freq=1.090e9,  # 1090 MHz (ADS-B)
        center_freq=96.3e6,  # 96.3 MHz (FM Radio)
        gain="auto",  # Auto gain
        buffer_size=262144,  # 256k samples per callback
    )

    network_config = NetworkConfig(
        host="0.0.0.0",  # Bind to all interfaces
        port=8080,  # TCP port
        max_clients=5,  # Max concurrent connections
    )

    # Create and start server
    server_instance = IQStreamServer(sdr_config, network_config)

    try:
        if server_instance.start_streaming():
            print("Server started successfully. Press Ctrl+C to stop.")
            # Keep main thread alive
            while server_instance.running:
                time.sleep(1)
        else:
            print("Failed to start server")

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        if server_instance:
            server_instance.stop_streaming()


if __name__ == "__main__":
    main()
