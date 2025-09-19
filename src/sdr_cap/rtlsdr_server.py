from rtlsdr import RtlSdrTcpServer


def main() -> None:
    # Create the TCP server connected to the local RTL-SDR device (index 0 by default)
    server = RtlSdrTcpServer(hostname='localhost', port=8080, device_index=0)

    # Important: Configure the underlying SDR device, not the server object itself.
    # The TCP client is the one intended to behave like RtlSdr and set these dynamically.
    try:
        sdr = server.sdr  # underlying RtlSdr instance
        sdr.sample_rate = 2.4e6  # 2.4 MHz
        sdr.center_freq = 1.09e9  # 1090 MHz
        sdr.gain = 'auto'  # or a numeric dB value, e.g., 27
    except AttributeError:
        print("Warning: underlying SDR handle not found on server; client must configure params.")

    print(f"Starting RTL-SDR TCP server on {server.hostname}:{server.port}")

    try:
        server.run_forever()
    except KeyboardInterrupt:
        print("Ctrl+C Entered: Shutting down server...")
    finally:
        server.close()
        print("Server closed.")


if __name__ == "__main__":
    main()