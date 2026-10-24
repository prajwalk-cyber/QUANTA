"""TLS 1.3 hybrid post-quantum client."""
import ssl
import time
import socket
from typing import Optional
from quanta_channel.policy import ChannelPolicy, PolicyMode
from quanta_channel.native_tls import set_ssl_context_groups, get_negotiated_group_name
from quanta_channel.channel import QuantaChannel
from quanta_channel.errors import CryptographicDowngradeError

class QuantaClient:
    """Establishes verified secure connections to QUANTA servers."""

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

        # Enforce strict certificate validation by default
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        ctx.load_verify_locations(self.cafile)

        # Enforce TLS 1.3 strictly
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3

        if self.client_cert and self.client_key:
            ctx.load_cert_chain(self.client_cert, self.client_key)

        # Configure hybrid post-quantum groups
        set_ssl_context_groups(ctx, self.policy.allowed_groups)
        return ctx

    def connect(
        self,
        host: str,
        port: int,
        server_hostname: Optional[str] = None,
        timeout: float = 10.0,
    ) -> QuantaChannel:
        """Connects to server, validates certificate chain, inspects group, and returns verified channel."""
        expected_hostname = server_hostname or host
        raw_sock = socket.create_connection((host, port), timeout=timeout)
        start = time.perf_counter()

        try:
            tls_sock = self._ctx.wrap_socket(raw_sock, server_hostname=expected_hostname)
        except Exception:
            raw_sock.close()
            raise

        handshake_ms = (time.perf_counter() - start) * 1000

        # Inspect negotiated group from TLS stack
        negotiated_group = get_negotiated_group_name(tls_sock)

        # Policy validation invariant: fails closed if downgrade attempt or unauthorized group
        try:
            self.policy.validate_negotiated_group(negotiated_group)
        except CryptographicDowngradeError:
            tls_sock.close()
            raise

        return QuantaChannel(
            sock=tls_sock,
            negotiated_group=negotiated_group,
            handshake_latency_ms=handshake_ms,
            is_server=False,
        )
