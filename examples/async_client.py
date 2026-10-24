#!/usr/bin/env python3
"""Standalone executable asynchronous QUANTA hybrid TLS 1.3 client."""
import sys
import os
import argparse
import asyncio

# Ensure quanta_channel is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "quanta-channel", "src")))

from quanta_channel import ChannelPolicy, PolicyMode
from quanta_channel.async_channel import AsyncQuantaClient

async def main():
    parser = argparse.ArgumentParser(description="QUANTA Async TLS 1.3 Hybrid Client")
    parser.add_argument("--host", default="127.0.0.1", help="Target server host")
    parser.add_argument("--port", type=int, default=44346, help="Target server port")
    parser.add_argument("--ca", default="certs/quanta_root_ca.crt", help="CA certificate file")
    parser.add_argument("--server-hostname", default="localhost", help="Expected server hostname")
    parser.add_argument("--message", default="Hello Post-Quantum World from Async Client!", help="Payload to send")
    parser.add_argument("--policy", choices=["STRICT_HYBRID", "CLASSICAL_PERMITTED"], default="STRICT_HYBRID")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ca_path = os.path.join(base_dir, args.ca)

    policy = ChannelPolicy(mode=PolicyMode(args.policy))
    client = AsyncQuantaClient(cafile=ca_path, policy=policy)

    print(f"[*] Connecting asynchronously to {args.host}:{args.port} [Expected SNI: {args.server_hostname}]...")
    async with await client.connect(args.host, args.port, server_hostname=args.server_hostname) as channel:
        print(f"[+] Async secure channel established!")
        print(f"    Negotiated Group:  {channel.negotiated_group}")
        print(f"    Handshake Latency: {channel.handshake_latency_ms:.2f} ms")

        print(f"[>] Sending: {args.message}")
        await channel.send_message(args.message.encode("utf-8"))

        reply = await channel.receive_message(timeout=10.0)
        print(f"[<] Received: {reply.decode('utf-8', errors='replace')}")
        print("[+] Async session completed cleanly.")

if __name__ == "__main__":
    asyncio.run(main())
