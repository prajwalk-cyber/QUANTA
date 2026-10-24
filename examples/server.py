#!/usr/bin/env python3
"""Standalone executable QUANTA hybrid TLS 1.3 server."""
import sys
import os
import argparse

# Ensure quanta_channel is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "quanta-channel", "src")))

from quanta_channel import QuantaServer, ChannelPolicy, PolicyMode

def main():
    parser = argparse.ArgumentParser(description="QUANTA TLS 1.3 Hybrid Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=44345, help="Port to listen on")
    parser.add_argument("--cert", default="certs/server.crt", help="Server certificate file")
    parser.add_argument("--key", default="certs/server.key", help="Server private key file")
    parser.add_argument("--policy", choices=["STRICT_HYBRID", "CLASSICAL_PERMITTED"], default="STRICT_HYBRID")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cert_path = os.path.join(base_dir, args.cert)
    key_path = os.path.join(base_dir, args.key)

    policy = ChannelPolicy(mode=PolicyMode(args.policy))
    server = QuantaServer(certfile=cert_path, keyfile=key_path, policy=policy)
    server.bind_and_listen(host=args.host, port=args.port)
    print(f"[*] QUANTA Server listening on {args.host}:{args.port} [Policy: {args.policy}]...")

    try:
        channel, addr = server.accept_channel(timeout=30.0)
        telemetry = channel.get_telemetry()
        print(f"[+] Client connected from {addr[0]}:{addr[1]}")
        print(f"    TLS Version:       {telemetry['tls_version']}")
        print(f"    Negotiated Group:  {telemetry['negotiated_group']}")
        print(f"    Cipher Suite:      {telemetry['cipher_suite']}")
        print(f"    Handshake Latency: {telemetry['handshake_latency_ms']} ms")

        msg = channel.receive_message(timeout=10.0)
        print(f"[<] Received message: {msg.decode('utf-8', errors='replace')}")

        reply = b"PQC_ACK: " + msg
        channel.send_message(reply)
        print(f"[>] Sent reply: {reply.decode('utf-8', errors='replace')}")
        channel.close()
        print("[+] Session closed cleanly.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
