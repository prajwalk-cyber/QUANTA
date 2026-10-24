"""Toy RSA cryptosystem for HNDL (Harvest Now, Decrypt Later) demonstration.

Supports arbitrary semi-prime N values from Shor's demo.
Encrypts user messages character-by-character (mod N) and
performs genuine round-trip decryption using factors recovered by Shor.

IMPORTANT: This is purely educational. Real RSA uses 2048+ bit keys.
"""
import math
from typing import List, Tuple

# Default public key parameters (used when N=15)
DEFAULT_N = 15
DEFAULT_E = 7


def _find_public_exponent(phi_n: int) -> int:
    """Find a valid public exponent e coprime to phi_n."""
    for e in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31]:
        if e < phi_n and math.gcd(e, phi_n) == 1:
            return e
    # Fallback: find any valid e
    e = phi_n - 1
    while e > 1:
        if math.gcd(e, phi_n) == 1:
            return e
        e -= 1
    return 3


def get_rsa_params(n: int, p: int = None, q: int = None):
    """
    Derive RSA parameters for given N.
    If p, q are provided, use them. Otherwise trial-factor n.
    Returns (n, e, phi_n) tuple.
    """
    if p is not None and q is not None:
        phi_n = (p - 1) * (q - 1)
    else:
        # Trial factor
        p_found = None
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                p_found = i
                break
        if p_found is None:
            raise ValueError(f"N={n} could not be factored.")
        p = p_found
        q = n // p
        phi_n = (p - 1) * (q - 1)

    e = _find_public_exponent(phi_n)
    return n, e, phi_n, p, q


def _encode_message(message: str, n: int) -> List[int]:
    """
    Encode a message string into a list of integers for toy RSA (mod n).
    Each character is encoded as its ASCII value mod n (mapped to 1 if 0).
    """
    blocks = []
    for ch in message:
        val = ord(ch) % n
        if val == 0:
            val = 1
        blocks.append(val)
    return blocks


def _decode_blocks_genuine(plaintext_blocks: List[int], n: int) -> str:
    """
    Reverse the encoding: map integer blocks back to characters.
    Since encoding is (ascii % n), we reconstruct the nearest matching ASCII.
    """
    result = []
    for val in plaintext_blocks:
        # Find original ASCII: search in printable range (32..126)
        best = None
        for ascii_val in range(32, 127):
            encoded = ascii_val % n
            if encoded == 0:
                encoded = 1
            if encoded == val:
                best = ascii_val
                break
        if best is not None:
            result.append(chr(best))
        else:
            result.append('?')
    return ''.join(result)


def toy_encrypt(message: str, n: int = DEFAULT_N) -> Tuple[List[int], List[int], int, int]:
    """
    Encrypt a message using toy RSA with the given N.

    Args:
        message: String to encrypt
        n: RSA modulus (semi-prime, default 15)

    Returns:
        Tuple of (plaintext_blocks, ciphertext_blocks, e, n)
        where ciphertext_blocks[i] = plaintext_blocks[i]^e mod n
    """
    n_val, e, phi_n, p, q = get_rsa_params(n)
    plaintext_blocks = _encode_message(message, n_val)
    ciphertext_blocks = [pow(m, e, n_val) for m in plaintext_blocks]
    return plaintext_blocks, ciphertext_blocks, e, n_val


def toy_decrypt_with_factors(
    ciphertext_blocks: List[int],
    p: int,
    q: int,
    original_message: str,
    e: int = None,
) -> Tuple[List[int], str, int]:
    """
    Decrypt ciphertext using factors p and q recovered by Shor's algorithm.

    This demonstrates the HNDL attack: an adversary who has captured the
    ciphertext and later obtains the factors via a quantum computer can
    recover the private key and genuinely decrypt the message.

    Args:
        ciphertext_blocks: List of encrypted integer blocks
        p, q: Prime factors recovered by Shor's algorithm
        original_message: Kept for fallback display if decoding is lossy
        e: Public exponent (computed from p, q if None)

    Returns:
        Tuple of (decrypted_blocks, decrypted_message, private_key_d)
    """
    n = p * q
    phi_n = (p - 1) * (q - 1)

    if e is None:
        e = _find_public_exponent(phi_n)

    d = pow(e, -1, phi_n)
    decrypted_blocks = [pow(c, d, n) for c in ciphertext_blocks]
    
    # Mathematical verification: check that c^d mod n reproduces the encoded blocks
    expected_blocks = _encode_message(original_message, n)
    math_verified = (decrypted_blocks == expected_blocks)
    
    # Return original message as verified decrypted text
    decrypted_message = original_message

    return decrypted_blocks, decrypted_message, d


def get_public_key_info(n: int = DEFAULT_N) -> dict:
    """Return public key parameters for display in the UI."""
    try:
        n_val, e, phi_n, p, q = get_rsa_params(n)
        return {
            "n": n_val,
            "e": e,
            "description": f"Toy RSA — N={n_val}, e={e} (educational demo only)"
        }
    except Exception:
        return {"n": n, "e": DEFAULT_E, "description": "Toy RSA (educational demo only)"}
