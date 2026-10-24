"""AES-GCM symmetric operations."""
import os
import time
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_gcm(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes, float]:
    """Encrypts plaintext using AES-GCM, returns (ciphertext, nonce, latency_ms)."""
    start = time.perf_counter()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    end = time.perf_counter()
    return ciphertext, nonce, round((end - start) * 1000, 2)

def decrypt_gcm(key: bytes, nonce: bytes, ciphertext: bytes) -> Tuple[bytes, bool, float]:
    """Decrypts ciphertext using AES-GCM, returns (plaintext, verified, latency_ms)."""
    start = time.perf_counter()
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        verified = True
    except Exception:
        plaintext = b""
        verified = False
    end = time.perf_counter()
    return plaintext, verified, round((end - start) * 1000, 2)
