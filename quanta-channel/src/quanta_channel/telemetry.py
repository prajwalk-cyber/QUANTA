"""Safe connection and cryptographic telemetry data structures."""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class SafeTelemetry:
    """Represents non-sensitive connection and cryptographic metadata."""
    tls_version: str
    negotiated_group: str
    cipher_suite: str
    handshake_latency_ms: float
    is_pqc_hybrid: bool
    is_server: bool
    peer_subject: str
    security_classification: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def build_safe_telemetry(
    sock,
    negotiated_group: str,
    latency_ms: float,
    is_server: bool = False
) -> SafeTelemetry:
    """Builds a SafeTelemetry object from an active TLS socket, guaranteeing no secret leaks."""
    cipher_tuple = sock.cipher() or ("UNKNOWN", "UNKNOWN", 0)
    tls_ver = sock.version() or "UNKNOWN"

    is_hybrid = "mlkem" in negotiated_group.lower()
    sec_class = "NIST Level 3 Post-Quantum Hybrid (FIPS 203)" if is_hybrid else "Classical Legacy Security"

    peercert = sock.getpeercert() or {}
    subject_str = "localhost"
    if peercert and "subject" in peercert:
        for rdn in peercert["subject"]:
            for key, val in rdn:
                if key == "commonName":
                    subject_str = val

    return SafeTelemetry(
        tls_version=tls_ver,
        negotiated_group=negotiated_group,
        cipher_suite=cipher_tuple[0],
        handshake_latency_ms=round(latency_ms, 2),
        is_pqc_hybrid=is_hybrid,
        is_server=is_server,
        peer_subject=subject_str,
        security_classification=sec_class
    )
