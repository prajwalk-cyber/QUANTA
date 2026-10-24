"""HKDF operations for QUANTA."""
import time
from typing import Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

def derive_hkdf(material: bytes, salt: bytes = None, length: int = 32) -> Tuple[bytes, float]:
    """Derives a key using HKDF-SHA256, returns (key, latency_ms)."""
    start = time.perf_counter()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=b"quanta-hybrid-kdf"
    )
    key = hkdf.derive(material)
    end = time.perf_counter()
    return key, round((end - start) * 1000, 2)
