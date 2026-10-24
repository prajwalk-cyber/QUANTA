"""Strongly-typed error hierarchy for the QUANTA secure channel."""

class QuantaError(Exception):
    """Base exception for all QUANTA channel errors."""
    pass

class CryptographicDowngradeError(QuantaError):
    """Raised when negotiated cryptographic parameters fail policy requirements."""
    pass

class UntrustedPeerCertificateError(QuantaError):
    """Raised when peer certificate cannot be verified against the trust root."""
    pass

class PeerIdentityMismatchError(QuantaError):
    """Raised when peer certificate Subject Alt Name does not match expected hostname."""
    pass

class OversizedFrameError(QuantaError):
    """Raised when received frame exceeds maximum allowable buffer size."""
    pass

class MalformedFrameError(QuantaError):
    """Raised when a received frame violates wire format invariants."""
    pass

class ConnectionClosedError(QuantaError):
    """Raised when the channel is closed by the peer or locally."""
    pass

class HandshakeTimeoutError(QuantaError):
    """Raised when connection or handshake exceeds configured timeout."""
    pass

class PQCConfigurationError(QuantaError):
    """Raised when post-quantum algorithms cannot be configured in the host runtime."""
    pass
