"""Unit tests for QNT1 binary framing protocol."""
import pytest
import struct
from quanta_channel.framing import encode_frame, parse_header, FrameType, MAGIC, HEADER_LENGTH, MAX_PAYLOAD_SIZE
from quanta_channel.errors import OversizedFrameError, MalformedFrameError

def test_encode_and_parse_valid_frame():
    payload = b"Hello Post-Quantum World"
    frame = encode_frame(FrameType.DATA, payload)
    assert len(frame) == HEADER_LENGTH + len(payload)
    assert frame[:4] == MAGIC

    ftype, flags, length = parse_header(frame[:HEADER_LENGTH])
    assert ftype == FrameType.DATA
    assert flags == 0
    assert length == len(payload)

def test_oversized_frame_rejection():
    # Attempting to encode payload exceeding 16 MiB must raise OversizedFrameError
    huge_len = MAX_PAYLOAD_SIZE + 10
    fake_header = struct.pack(">4sBHI", MAGIC, int(FrameType.DATA), 0, huge_len)
    with pytest.raises(OversizedFrameError) as excinfo:
        parse_header(fake_header)
    assert "exceeding maximum limit" in str(excinfo.value)

def test_invalid_magic_rejection():
    corrupted_header = b"BAD1" + b"\x01\x00\x00\x00\x00\x00\x05"
    with pytest.raises(MalformedFrameError) as excinfo:
        parse_header(corrupted_header)
    assert "Invalid frame magic" in str(excinfo.value)

def test_truncated_header_rejection():
    short_header = b"QNT1\x01\x00"
    with pytest.raises(MalformedFrameError):
        parse_header(short_header)

def test_control_frame_types():
    for ftype in [FrameType.PING, FrameType.PONG, FrameType.CLOSE]:
        frame = encode_frame(ftype)
        parsed_type, _, length = parse_header(frame[:HEADER_LENGTH])
        assert parsed_type == ftype
        assert length == 0
