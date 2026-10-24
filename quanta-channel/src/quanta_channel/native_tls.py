"""Low-level OpenSSL 3.6+ integration for TLS 1.3 hybrid key exchange."""
import ssl
import ctypes
import ctypes.util
from typing import Optional, List
from quanta_channel.errors import PQCConfigurationError

# Load OpenSSL libssl.so.3
_LIBSSL_PATH = ctypes.util.find_library("ssl") or "libssl.so.3"
try:
    _libssl = ctypes.CDLL(_LIBSSL_PATH)
except OSError as e:
    raise RuntimeError(f"Unable to load OpenSSL library '{_LIBSSL_PATH}': {e}")

# Bind SSL_CTX_ctrl (for SSL_CTRL_SET_GROUPS_LIST = 92)
_libssl.SSL_CTX_ctrl.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long, ctypes.c_char_p]
_libssl.SSL_CTX_ctrl.restype = ctypes.c_long

# Bind SSL_get0_group_name (OpenSSL 3.2+)
if hasattr(_libssl, "SSL_get0_group_name"):
    _libssl.SSL_get0_group_name.argtypes = [ctypes.c_void_p]
    _libssl.SSL_get0_group_name.restype = ctypes.c_char_p
    _HAS_GET0_GROUP = True
else:
    _HAS_GET0_GROUP = False

SSL_CTRL_SET_GROUPS_LIST = 92

def set_ssl_context_groups(ctx: ssl.SSLContext, groups: List[str]) -> None:
    """Configures supported TLS 1.3 key-exchange groups on an SSLContext using OpenSSL C API."""
    if not groups:
        return
    groups_str = ":".join(groups)
    # PySSLContext layout: PyObject_HEAD (16 bytes), then SSL_CTX* ctx at offset 16
    ctx_ptr = ctypes.c_void_p.from_address(id(ctx) + 16).value
    if not ctx_ptr:
        raise PQCConfigurationError("Failed to extract native SSL_CTX pointer from SSLContext.")

    ret = _libssl.SSL_CTX_ctrl(ctx_ptr, SSL_CTRL_SET_GROUPS_LIST, 0, groups_str.encode("utf-8"))
    if ret != 1:
        raise PQCConfigurationError(
            f"Failed to configure TLS groups '{groups_str}'. Ensure host OpenSSL supports these algorithms."
        )

def get_negotiated_group_name(sslsock: ssl.SSLSocket) -> Optional[str]:
    """Inspects the active SSL connection and returns the negotiated group name."""
    if not _HAS_GET0_GROUP:
        return None
    # PySSLSocket layout: _sslobj holds PySSLObject; SSL* ssl is at offset 24 in PySSLObject
    sslobj = getattr(sslsock, "_sslobj", None)
    if not sslobj:
        return None
    ssl_ptr = ctypes.c_void_p.from_address(id(sslobj) + 24).value
    if not ssl_ptr:
        return None
    res = _libssl.SSL_get0_group_name(ssl_ptr)
    if res:
        return res.decode("utf-8")
    return None


class OpenSSLNativeHelper:
    """Helper for querying native OpenSSL library capabilities and supported groups."""

    @property
    def version_str(self) -> str:
        return getattr(ssl, "OPENSSL_VERSION", "Unknown OpenSSL")

    @classmethod
    def get_openssl_version(cls) -> str:
        return getattr(ssl, "OPENSSL_VERSION", "Unknown OpenSSL")

    @classmethod
    def has_group(cls, group_name: str) -> bool:
        """Tests whether host OpenSSL accepts the group name in SSL_CTX_ctrl."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx_ptr = ctypes.c_void_p.from_address(id(ctx) + 16).value
            if not ctx_ptr:
                return False
            ret = _libssl.SSL_CTX_ctrl(ctx_ptr, SSL_CTRL_SET_GROUPS_LIST, 0, group_name.encode("utf-8"))
            return ret == 1
        except Exception:
            return False

    @classmethod
    def get_supported_pqc_groups(cls) -> List[str]:
        candidates = ["X25519MLKEM768", "MLKEM768", "MLKEM1024", "MLKEM512", "SecP256r1MLKEM768"]
        return [g for g in candidates if cls.has_group(g)]

