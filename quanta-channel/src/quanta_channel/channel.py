"""Established secure channel representation and frame I/O."""
import ssl
import time
import socket
from typing import Optional, Dict, Any
from quanta_channel.framing import encode_frame, parse_header, FrameType, HEADER_LENGTH
from quanta_channel.errors import ConnectionClosedError, MalformedFrameError, OversizedFrameError

class QuantaChannel:
    """Manages full-duplex communication over an established, verified TLS 1.3 channel."""

    def __init__(
        self,
        sock: ssl.SSLSocket,
        negotiated_group: str,
        handshake_latency_ms: float = 0.0,
        is_server: bool = False,
    ):
        self._sock = sock
        self.negotiated_group = negotiated_group
        self.handshake_latency_ms = handshake_latency_ms
        self.is_server = is_server
        self._is_closed = False

    def send_message(self, payload: bytes) -> None:
        """Sends an application data message encapsulated in a QNT1 frame."""
        if self._is_closed:
            raise ConnectionClosedError("Cannot send on closed channel.")
        frame = encode_frame(FrameType.DATA, payload)
        self._sock.sendall(frame)

    def send_ping(self) -> None:
        """Sends a keepalive PING frame."""
        if self._is_closed:
            raise ConnectionClosedError("Cannot send on closed channel.")
        frame = encode_frame(FrameType.PING)
        self._sock.sendall(frame)

    def _read_exact(self, num_bytes: int, timeout: Optional[float] = None) -> bytes:
        """Reads exactly num_bytes from the underlying TLS stream."""
        if timeout is not None:
            self._sock.settimeout(timeout)
        buf = bytearray()
        while len(buf) < num_bytes:
            chunk = self._sock.recv(num_bytes - len(buf))
            if not chunk:
                self._is_closed = True
                raise ConnectionClosedError("Connection terminated by peer.")
            buf.extend(chunk)
        return bytes(buf)

    def receive_message(self, timeout: Optional[float] = 10.0) -> bytes:
        """Receives the next complete application data payload, handling control frames."""
        while not self._is_closed:
            header_bytes = self._read_exact(HEADER_LENGTH, timeout=timeout)
            frame_type, flags, payload_len = parse_header(header_bytes)

            payload = self._read_exact(payload_len, timeout=timeout) if payload_len > 0 else b""

            if frame_type == FrameType.DATA:
                return payload
            elif frame_type == FrameType.PING:
                # Reply immediately with PONG
                pong = encode_frame(FrameType.PONG)
                self._sock.sendall(pong)
            elif frame_type == FrameType.PONG:
                continue
            elif frame_type == FrameType.CLOSE:
                self.close()
                raise ConnectionClosedError("Channel gracefully closed by peer.")
            else:
                continue

        raise ConnectionClosedError("Channel is closed.")

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns safe, non-sensitive connection and cryptographic telemetry."""
        cipher_info = self._sock.cipher()
        return {
            "tls_version": self._sock.version(),
            "negotiated_group": self.negotiated_group,
            "cipher_suite": cipher_info[0] if cipher_info else "UNKNOWN",
            "cipher_bits": cipher_info[2] if cipher_info else 0,
            "handshake_latency_ms": round(self.handshake_latency_ms, 2),
            "is_server": self.is_server,
            "peer_certificate": self._sock.getpeercert(),
        }

    def close(self) -> None:
        """Gracefully closes the channel."""
        if not self._is_closed:
            try:
                close_frame = encode_frame(FrameType.CLOSE)
                self._sock.sendall(close_frame)
            except Exception:
                pass
            try:
                self._sock.close()
            except Exception:
                pass
            self._is_closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
