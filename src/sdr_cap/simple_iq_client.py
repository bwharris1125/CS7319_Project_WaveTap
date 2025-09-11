import os
import socket
import struct
import sys

HOST = os.getenv("IQ_HOST", "localhost")
PORT = int(os.getenv("IQ_PORT", 8080))
MAX_PACKETS = int(os.getenv("IQ_MAX_PACKETS", 5))

if len(sys.argv) > 1:
    HOST = sys.argv[1]
if len(sys.argv) > 2:
    PORT = int(sys.argv[2])
if len(sys.argv) > 3:
    MAX_PACKETS = int(sys.argv[3])

print(f"Connecting to {HOST}:{PORT} ...")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print("Connected.")

    for i in range(MAX_PACKETS):
        # Read 4-byte header (big-endian uint32 sample count)
        header = b""
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                print("Connection closed by server (header)")
                sys.exit(1)
            header += chunk
        sample_count = struct.unpack(">I", header)[0]

        # Read IQ data (sample_count * 2 * 4 bytes)
        data_len = sample_count * 2 * 4
        data = b""
        while len(data) < data_len:
            chunk = sock.recv(data_len - len(data))
            if not chunk:
                print("Connection closed by server (data)")
                sys.exit(1)
            data += chunk
        print(
            f"Packet {i + 1}: Received {sample_count} samples ({len(data)} bytes)"
        )

    print("Done. Closing socket.")
    sock.close()
except Exception as e:
    if e.errno == 111:  # Connection refused
        print("[Errno 111] Connection refused, check if server is running.")
    else:
        print(f"Error: {e}")
    exit()
