#!/usr/bin/env python3
"""Standalone executable asynchronous QUANTA hybrid TLS 1.3 server."""
import sys
import os
import argparse
import asyncio

# Ensure quanta_channel is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "quanta-channel", "src")))

from quanta_channel import ChannelPolicy, PolicyMode
from quanta_channel.async_channel import AsyncQuantaChannel
from quanta_channel.native_tls import set_ssl_context_groups, get_negotiated_group_name
import ssl

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, policy: ChannelPolicy):
    tls_sock = writer.get_extra_info("ssl_object")
    group = get_negotiated_group_name(tls_sock)
    try:
        policy.validate_negotiated_group(group)
    except Exception as exc:
        print(f"[!] Policy validation failed: {exc}")
        writer.close()
        await writer.wait_closed()
        return

    channel = AsyncQuantaChannel(reader, writer, negotiated_group=group, is_server=True)
    addr = writer.get_extra_info("peername")
    print(f"[+] Client connected from {addr[0]}:{addr[1]} [Group: {group}]")

    try:
        msg = await channel.receive_message(timeout=10.0)
        print(f"[<] Received: {msg.decode('utf-8', errors='replace')}")
        reply = b"ASYNC_PQC_ACK: " + msg
        await channel.send_message(reply)
        print(f"[>] Sent: {reply.decode('utf-8', errors='replace')}")
    finally:
        await channel.close()
        print("[+] Async session closed cleanly.")

async def main():
    parser = argparse.ArgumentParser(description="QUANTA Async TLS 1.3 Hybrid Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=44346, help="Port to listen on")
    parser.add_argument("--cert", default="certs/server.crt", help="Server certificate file")
    parser.add_argument("--key", default="certs/server.key", help="Server private key file")
    parser.add_argument("--policy", choices=["STRICT_HYBRID", "CLASSICAL_PERMITTED"], default="STRICT_HYBRID")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cert_path = os.path.join(base_dir, args.cert)
    key_path = os.path.join(base_dir, args.key)

    policy = ChannelPolicy(mode=PolicyMode(args.policy))
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(cert_path, key_path)
    set_ssl_context_groups(ctx, policy.allowed_groups)

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, policy),
        host=args.host,
        port=args.port,
        ssl=ctx,
    )

    print(f"[*] Async QUANTA Server listening on {args.host}:{args.port} [Policy: {args.policy}]...")
    async with server:
        # Serve one connection for demonstration
        await asyncio.sleep(0.1)
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
