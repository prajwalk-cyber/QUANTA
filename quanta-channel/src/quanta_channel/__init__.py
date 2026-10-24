"""QUANTA Secure Channel Library.

Provides standards-compliant post-quantum hybrid TLS 1.3 secure communication.
"""

from quanta_channel.channel import QuantaChannel
from quanta_channel.client import QuantaClient
from quanta_channel.server import QuantaServer
from quanta_channel.async_channel import AsyncQuantaChannel, AsyncQuantaClient
from quanta_channel.policy import ChannelPolicy, PolicyMode
from quanta_channel.telemetry import SafeTelemetry
from quanta_channel.native_tls import OpenSSLNativeHelper
from quanta_channel.errors import (
    QuantaError,
    CryptographicDowngradeError,
    UntrustedPeerCertificateError,
    PeerIdentityMismatchError,
    OversizedFrameError,
    MalformedFrameError,
    ConnectionClosedError,
    HandshakeTimeoutError,
    PQCConfigurationError,
)

__version__ = "0.2.0"
__all__ = [
    "QuantaChannel",
    "QuantaClient",
    "QuantaServer",
    "AsyncQuantaChannel",
    "AsyncQuantaClient",
    "ChannelPolicy",
    "PolicyMode",
    "SafeTelemetry",
    "OpenSSLNativeHelper",
    "QuantaError",
    "CryptographicDowngradeError",
    "UntrustedPeerCertificateError",
    "PeerIdentityMismatchError",
    "OversizedFrameError",
    "MalformedFrameError",
    "ConnectionClosedError",
    "HandshakeTimeoutError",
    "PQCConfigurationError",
]
