"""Asynchronous TLS 1.3 post-quantum hybrid secure channel implementation."""
import ssl
import time
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from quanta_channel.policy import ChannelPolicy, PolicyMode
from quanta_channel.native_tls import set_ssl_context_groups, get_negotiated_group_name
from quanta_channel.framing import encode_frame, parse_header, FrameType, HEADER_LENGTH
from quanta_channel.telemetry import SafeTelemetry, build_safe_telemetry
from quanta_channel.errors import (
    ConnectionClosedError,
    CryptographicDowngradeError,
    MalformedFrameError,
    OversizedFrameError,
)

class AsyncQuantaChannel:
    """Manages asynchronous communication over an established TLS 1.3 hybrid connection."""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        negotiated_group: str,
        handshake_latency_ms: float = 0.0,
        is_server: bool = False,
    ):
        self._reader = reader
        self._writer = writer
        self.negotiated_group = negotiated_group
        self.handshake_latency_ms = handshake_latency_ms
        self.is_server = is_server
        self._is_closed = False

    async def send_message(self, payload: bytes) -> None:
        """Sends an application data message encapsulated in a QNT1 frame."""
        if self._is_closed:
            raise ConnectionClosedError("Cannot send on closed channel.")
        frame = encode_frame(FrameType.DATA, payload)
        self._writer.write(frame)
        await self._writer.drain()

    async def send_ping(self) -> None:
        """Sends a keepalive PING frame."""
        if self._is_closed:
            raise ConnectionClosedError("Cannot send on closed channel.")
        frame = encode_frame(FrameType.PING)
        self._writer.write(frame)
        await self._writer.drain()

    async def _read_exact(self, num_bytes: int, timeout: Optional[float] = None) -> bytes:
        """Reads exactly num_bytes asynchronously from the stream."""
        try:
            if timeout is not None:
                data = await asyncio.wait_for(self._reader.readexactly(num_bytes), timeout=timeout)
            else:
                data = await self._reader.readexactly(num_bytes)
            return data
        except (asyncio.IncompleteReadError, ConnectionResetError):
            self._is_closed = True
            raise ConnectionClosedError("Connection terminated by peer.")

    async def receive_message(self, timeout: Optional[float] = 10.0) -> bytes:
        """Receives the next complete application data payload, handling control frames."""
        while not self._is_closed:
            header_bytes = await self._read_exact(HEADER_LENGTH, timeout=timeout)
            frame_type, flags, payload_len = parse_header(header_bytes)

            payload = await self._read_exact(payload_len, timeout=timeout) if payload_len > 0 else b""

            if frame_type == FrameType.DATA:
                return payload
            elif frame_type == FrameType.PING:
                pong = encode_frame(FrameType.PONG)
                self._writer.write(pong)
                await self._writer.drain()
            elif frame_type == FrameType.PONG:
                continue
            elif frame_type == FrameType.CLOSE:
                await self.close()
                raise ConnectionClosedError("Channel gracefully closed by peer.")
            else:
                continue

        raise ConnectionClosedError("Channel is closed.")

    def get_telemetry(self) -> SafeTelemetry:
        """Returns safe, non-sensitive connection and cryptographic telemetry."""
        sslobj = self._writer.get_extra_info("ssl_object")
        return build_safe_telemetry(
            sock=sslobj,
            negotiated_group=self.negotiated_group,
            latency_ms=self.handshake_latency_ms,
            is_server=self.is_server,
        )

    async def close(self) -> None:
        """Gracefully closes the channel."""
        if not self._is_closed:
            try:
                close_frame = encode_frame(FrameType.CLOSE)
                self._writer.write(close_frame)
                await self._writer.drain()
            except Exception:
                pass
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._is_closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

class AsyncQuantaClient:
    """Asynchronous client establishing verified TLS 1.3 hybrid connections."""

    def __init__(
        self,
        cafile: str,
        policy: Optional[ChannelPolicy] = None,
        client_cert: Optional[str] = None,
        client_key: Optional[str] = None,
    ):
        self.cafile = cafile
        self.policy = policy or ChannelPolicy(mode=PolicyMode.STRICT_HYBRID)
        self.client_cert = client_cert
        self.client_key = client_key
        self._ctx = self._create_ssl_context()

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        ctx.load_verify_locations(self.cafile)

        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3

        if self.client_cert and self.client_key:
            ctx.load_cert_chain(self.client_cert, self.client_key)

        set_ssl_context_groups(ctx, self.policy.allowed_groups)
        return ctx

    async def connect(
        self,
        host: str,
        port: int,
        server_hostname: Optional[str] = None,
        timeout: float = 10.0,
    ) -> AsyncQuantaChannel:
        """Asynchronously establishes a verified hybrid TLS 1.3 connection."""
        expected_hostname = server_hostname or host
        start = time.perf_counter()

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=self._ctx, server_hostname=expected_hostname),
            timeout=timeout,
        )
        handshake_ms = (time.perf_counter() - start) * 1000

        sslobj = writer.get_extra_info("ssl_object")
        negotiated_group = get_negotiated_group_name(sslobj)

        try:
            self.policy.validate_negotiated_group(negotiated_group)
        except CryptographicDowngradeError:
            writer.close()
            await writer.wait_closed()
            raise

        return AsyncQuantaChannel(
            reader=reader,
            writer=writer,
            negotiated_group=negotiated_group,
            handshake_latency_ms=handshake_ms,
            is_server=False,
        )
