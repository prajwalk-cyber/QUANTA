"""TLS 1.3 hybrid post-quantum server."""
import ssl
import time
import socket
from typing import Optional, Tuple
from quanta_channel.policy import ChannelPolicy, PolicyMode
from quanta_channel.native_tls import set_ssl_context_groups, get_negotiated_group_name
from quanta_channel.channel import QuantaChannel
from quanta_channel.errors import CryptographicDowngradeError

class QuantaServer:
    """Listens for and accepts secure TLS 1.3 hybrid connections."""

    def __init__(
        self,
        certfile: str,
        keyfile: str,
        policy: Optional[ChannelPolicy] = None,
        cafile: Optional[str] = None,
        require_client_cert: bool = False,
    ):
        self.certfile = certfile
        self.keyfile = keyfile
        self.policy = policy or ChannelPolicy(mode=PolicyMode.STRICT_HYBRID)
        self.cafile = cafile
        self.require_client_cert = require_client_cert
        self._ctx = self._create_ssl_context()
        self._server_sock: Optional[socket.socket] = None

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(self.certfile, self.keyfile)

        # Enforce TLS 1.3 strictly
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3

        if self.require_client_cert and self.cafile:
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.load_verify_locations(self.cafile)

        # Configure hybrid post-quantum groups
        set_ssl_context_groups(ctx, self.policy.allowed_groups)
        return ctx

    def bind_and_listen(self, host: str = "127.0.0.1", port: int = 4433, backlog: int = 128) -> socket.socket:
        """Binds to the host and port and starts listening."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(backlog)
        self._server_sock = sock
        return sock

    def accept_channel(self, timeout: Optional[float] = None) -> Tuple[QuantaChannel, Tuple[str, int]]:
        """Accepts an incoming client connection, performs handshake, and returns a verified channel."""
        if not self._server_sock:
            raise RuntimeError("Server socket not bound. Call bind_and_listen() first.")

        if timeout is not None:
            self._server_sock.settimeout(timeout)

        raw_conn, addr = self._server_sock.accept()
        start = time.perf_counter()

        # Wrap in TLS 1.3
        tls_conn = self._ctx.wrap_socket(raw_conn, server_side=True)
        handshake_ms = (time.perf_counter() - start) * 1000

        # Inspect negotiated group and validate policy
        negotiated_group = get_negotiated_group_name(tls_conn)
        self.policy.validate_negotiated_group(negotiated_group)

        channel = QuantaChannel(
            sock=tls_conn,
            negotiated_group=negotiated_group,
            handshake_latency_ms=handshake_ms,
            is_server=True,
        )
        return channel, addr

    def close(self) -> None:
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None
