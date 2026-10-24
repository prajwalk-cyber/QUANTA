#!/usr/bin/env python3
"""Standalone executable QUANTA hybrid TLS 1.3 client."""
import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "quanta-channel", "src")))

from quanta_channel import QuantaClient, ChannelPolicy, PolicyMode

def main():
    parser = argparse.ArgumentParser(description="QUANTA TLS 1.3 Hybrid Client")
    parser.add_argument("--host", default="127.0.0.1", help="Target server host")
    parser.add_argument("--port", type=int, default=44345, help="Target server port")
    parser.add_argument("--ca", default="certs/quanta_root_ca.crt", help="CA certificate file")
    parser.add_argument("--server-hostname", default="localhost", help="Expected server hostname")
    parser.add_argument("--message", default="Hello Post-Quantum World from QUANTA Client!", help="Payload to send")
    parser.add_argument("--policy", choices=["STRICT_HYBRID", "CLASSICAL_PERMITTED"], default="STRICT_HYBRID")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ca_path = os.path.join(base_dir, args.ca)

    policy = ChannelPolicy(mode=PolicyMode(args.policy))
    client = QuantaClient(cafile=ca_path, policy=policy)

    print(f"[*] Connecting to {args.host}:{args.port} [Expected SNI: {args.server_hostname}]...")
    with client.connect(args.host, args.port, server_hostname=args.server_hostname) as channel:
        telemetry = channel.get_telemetry()
        print(f"[+] Secure channel established!")
        print(f"    TLS Version:       {telemetry['tls_version']}")
        print(f"    Negotiated Group:  {telemetry['negotiated_group']}")
        print(f"    Cipher Suite:      {telemetry['cipher_suite']}")
        print(f"    Handshake Latency: {telemetry['handshake_latency_ms']} ms")

        print(f"[>] Sending: {args.message}")
        channel.send_message(args.message.encode("utf-8"))

        reply = channel.receive_message(timeout=10.0)
        print(f"[<] Received: {reply.decode('utf-8', errors='replace')}")
        print("[+] Session closed cleanly.")

if __name__ == "__main__":
    main()
