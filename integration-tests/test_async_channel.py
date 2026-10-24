"""Asynchronous integration test for AsyncQuantaClient and AsyncQuantaChannel."""
import os
import sys
import ssl
import pytest
import asyncio

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "quanta-channel", "src"))

from quanta_channel import AsyncQuantaClient, ChannelPolicy, PolicyMode
from quanta_channel.native_tls import set_ssl_context_groups, get_negotiated_group_name

CERT = os.path.join(BASE_DIR, "certs", "server.crt")
KEY = os.path.join(BASE_DIR, "certs", "server.key")
CA = os.path.join(BASE_DIR, "certs", "quanta_root_ca.crt")
PORT = 44380

@pytest.mark.asyncio
async def test_async_hybrid_channel_roundtrip():
    # 1. Start Async TLS 1.3 Server
    s_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    s_ctx.load_cert_chain(CERT, KEY)
    s_ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    set_ssl_context_groups(s_ctx, ["X25519MLKEM768"])

    server_received = []

    async def client_handler(reader, writer):
        from quanta_channel.framing import encode_frame, parse_header, FrameType, HEADER_LENGTH
        header = await reader.readexactly(HEADER_LENGTH)
        ftype, flags, length = parse_header(header)
        payload = await reader.readexactly(length)
        server_received.append(payload)

        # Echo back with prefix
        reply = encode_frame(FrameType.DATA, b"ASYNC_PQC_ACK: " + payload)
        writer.write(reply)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    srv = await asyncio.start_server(client_handler, "127.0.0.1", PORT, ssl=s_ctx)

    # 2. Connect with AsyncQuantaClient
    client = AsyncQuantaClient(cafile=CA, policy=ChannelPolicy(mode=PolicyMode.STRICT_HYBRID))

    async with await client.connect("127.0.0.1", PORT, server_hostname="localhost") as channel:
        telemetry = channel.get_telemetry()
        assert telemetry.negotiated_group == "X25519MLKEM768"
        assert telemetry.is_pqc_hybrid == True
        assert telemetry.tls_version == "TLSv1.3"

        test_msg = b"ASYNC_HYBRID_MESSAGE_2026"
        await channel.send_message(test_msg)
        response = await channel.receive_message(timeout=5.0)

        assert response == b"ASYNC_PQC_ACK: " + test_msg
        assert server_received[0] == test_msg

    srv.close()
    await srv.wait_closed()
