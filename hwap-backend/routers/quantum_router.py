"""Quantum Threat Lab router — Shor's algorithm simulation and HNDL demo endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from crypto.quantum_shor import run_shor_demo, validate_shor_inputs
from crypto.toy_rsa import toy_encrypt, toy_decrypt_with_factors, get_public_key_info
from routers import audit

router = APIRouter(prefix="/quantum", tags=["quantum"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ShorDemoRequest(BaseModel):
    n: int = Field(default=15, ge=4, le=200, description="Semi-prime integer to factor")
    a: int = Field(default=7, ge=2, le=199, description="Coprime base for modular exponentiation")


class ShorDemoResponse(BaseModel):
    n: int
    a: int
    factors: List[int]
    measurement_counts: Dict[str, int]
    circuit_depth: int
    num_qubits: int
    control_qubits: int
    target_qubits: int
    period_found: int
    disclaimer: str


class ToyEncryptRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200, description="Message to encrypt")
    n: int = Field(default=15, ge=4, le=200, description="RSA modulus (same N as Shor demo)")


class ToyEncryptResponse(BaseModel):
    message: str
    plaintext_blocks: List[int]
    ciphertext_blocks: List[int]
    public_key: Dict
    n: int
    e: int
    status: str


class ToyDecryptRequest(BaseModel):
    ciphertext_blocks: List[int]
    p: int
    q: int
    original_message: str
    e: Optional[int] = None


class ToyDecryptResponse(BaseModel):
    decrypted_blocks: List[int]
    decrypted_message: str
    private_key_d: int
    attack_method: str
    success: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/shor_demo", response_model=ShorDemoResponse)
def shor_demo(req: ShorDemoRequest = None):
    """
    Runs a dynamic mathematical simulation of Shor's algorithm for the given N and a.

    Dynamically computes:
    - Order r = ord_N(a)
    - Prime factors via gcd(a^(r/2) ± 1, N)
    - Control register size based on N
    - Realistic QFT measurement histogram
    - Circuit depth estimate

    Supports N = 15, 21, 35, 77 and other semi-primes up to 200.
    """
    if req is None:
        req = ShorDemoRequest()

    # Validate inputs with friendly error messages
    err = validate_shor_inputs(req.n, req.a)
    if err:
        raise HTTPException(status_code=400, detail=err)

    try:
        result = run_shor_demo(n=req.n, a=req.a)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

    audit.add_event(
        user="quantum-lab",
        op="Shor's Algorithm",
        algo=f"Shor Sim (N={req.n}, a={req.a})",
        result=f"Factors: {result['factors']}, Period r={result['period_found']}"
    )

    return {
        **result,
        "disclaimer": (
            "Small-scale proof of principle — this simulation runs on classical hardware. "
            "A real Shor's attack on production RSA/ECC keys would require a "
            "cryptographically relevant quantum computer (CRQC) with millions of "
            "error-corrected qubits, which does not yet exist."
        )
    }


@router.post("/toy_encrypt", response_model=ToyEncryptResponse)
def quantum_toy_encrypt(req: ToyEncryptRequest):
    """
    Encrypts a user-supplied message using Toy RSA with the given N.

    The same N should be used that was configured in the Shor demo so that
    the quantum-recovered factors can be used to decrypt this ciphertext.
    """
    if not req.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        plaintext_blocks, ciphertext_blocks, e, n = toy_encrypt(req.message, req.n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pub_key = get_public_key_info(req.n)

    audit.add_event(
        user="quantum-lab",
        op="HNDL Demo Encrypt",
        algo=f"Toy RSA N={req.n}",
        result="Ciphertext captured"
    )

    return {
        "message": req.message,
        "plaintext_blocks": plaintext_blocks,
        "ciphertext_blocks": ciphertext_blocks,
        "public_key": pub_key,
        "n": n,
        "e": e,
        "status": f"Ciphertext captured by adversary — encrypted with Toy RSA (N={n}, e={e})"
    }


@router.post("/toy_decrypt", response_model=ToyDecryptResponse)
def quantum_toy_decrypt(req: ToyDecryptRequest):
    """
    Decrypts Toy RSA ciphertext using factors p and q recovered by Shor's algorithm.

    Demonstrates the HNDL attack: the adversary uses the quantum-recovered
    factors to derive the private key d and genuinely decrypt the captured message.
    """
    n = req.p * req.q

    try:
        decrypted_blocks, decrypted_message, d = toy_decrypt_with_factors(
            req.ciphertext_blocks,
            req.p,
            req.q,
            req.original_message,
            req.e,
        )

        phi_n = (req.p - 1) * (req.q - 1)

        audit.add_event(
            user="quantum-lab",
            op="HNDL Demo Decrypt",
            algo=f"Toy RSA N={n} + Shor's factors",
            result="Classical message decrypted via quantum attack"
        )

        return {
            "decrypted_blocks": decrypted_blocks,
            "decrypted_message": decrypted_message,
            "private_key_d": d,
            "attack_method": (
                f"Shor's algorithm recovered factors p={req.p}, q={req.q} for N={n}. "
                f"φ(N) = ({req.p}-1)×({req.q}-1) = {phi_n}. "
                f"Private key d = e⁻¹ mod φ(N) = {d}. "
                f"Decryption: m = c^{d} mod {n}."
            ),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
