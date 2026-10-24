"""Bounded binary framing protocol (QNT1) for QUANTA secure channels."""
import struct
from enum import IntEnum
from typing import Tuple, Optional
from quanta_channel.errors import OversizedFrameError, MalformedFrameError

MAGIC = b"QNT1"
HEADER_LENGTH = 11  # 4B magic + 1B type + 2B flags + 4B length
MAX_PAYLOAD_SIZE = 16 * 1024 * 1024  # 16 MiB

class FrameType(IntEnum):
    DATA = 0x01
    PING = 0x02
    PONG = 0x03
    KEY_UPDATE = 0x04
    CLOSE = 0x05

def encode_frame(frame_type: FrameType, payload: bytes = b"", flags: int = 0) -> bytes:
    """Encodes a bounded QNT1 binary frame."""
    payload_len = len(payload)
    if payload_len > MAX_PAYLOAD_SIZE:
        raise OversizedFrameError(
            f"Payload size {payload_len} bytes exceeds maximum allowed limit ({MAX_PAYLOAD_SIZE} bytes)."
        )
    header = struct.pack(">4sBHI", MAGIC, int(frame_type), flags, payload_len)
    return header + payload

def parse_header(header_bytes: bytes) -> Tuple[FrameType, int, int]:
    """Parses and validates an 11-byte QNT1 frame header.

    Returns:
        Tuple of (frame_type, flags, payload_length)
    """
    if len(header_bytes) != HEADER_LENGTH:
        raise MalformedFrameError(f"Header must be {HEADER_LENGTH} bytes, got {len(header_bytes)}.")

    magic, type_int, flags, payload_len = struct.unpack(">4sBHI", header_bytes)
    if magic != MAGIC:
        raise MalformedFrameError(f"Invalid frame magic: expected {MAGIC!r}, received {magic!r}.")

    try:
        frame_type = FrameType(type_int)
    except ValueError:
        raise MalformedFrameError(f"Unknown frame type: {hex(type_int)}.")

    if payload_len > MAX_PAYLOAD_SIZE:
        raise OversizedFrameError(
            f"Frame header specifies payload length of {payload_len} bytes, exceeding maximum limit ({MAX_PAYLOAD_SIZE} bytes)."
        )

    return frame_type, flags, payload_len
