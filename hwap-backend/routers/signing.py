"""Signing routers."""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from models.schemas import SignRequest, SignResponse, VerifyRequest, VerifyResponse
from crypto.signatures import sign_message, verify_signature, OQS_AVAILABLE
from routers import audit
import uuid
import datetime

router = APIRouter(prefix="/api")

# Stores {sig_id: {hex, message, user_id, public_key_hex}}
SIGNATURES_DB = {}


@router.post("/sign", response_model=SignResponse)
async def sign_route(req: SignRequest):
    """Signs a message and stores signature metadata."""
    res = sign_message(req.message, req.user_id)
    sig_id = str(uuid.uuid4())
    SIGNATURES_DB[sig_id] = {
        "hex": res["signature_hex"],
        "message": req.message,
        "user_id": req.user_id,
    }
    audit.add_event(
        user=req.user_id[:20],
        op="Signing",
        algo="ML-DSA-65",
        result="Success"
    )
    return {
        "signature_id": sig_id,
        "signature_hex": res["signature_hex"],
        "algorithm": "ML-DSA-65",
        "sig_size_bytes": res["sig_size_bytes"],
        "sign_latency_ms": res["sign_latency_ms"],
    }


@router.post("/verify", response_model=VerifyResponse)
async def verify_route(req: VerifyRequest):
    """Verifies a signature against the stored message."""
    entry = SIGNATURES_DB.get(req.signature_id)
    if not entry:
        return {"valid": False, "signer_id": "", "timestamp": "", "integrity": "tampered"}

    if OQS_AVAILABLE and req.public_key_hex:
        res = verify_signature(req.message, entry["hex"], req.public_key_hex)
        valid = res["valid"]
    else:
        # Fallback: valid only when exact same message is submitted
        valid = req.message == entry["message"]

    result = "Valid" if valid else "Invalid"
    audit.add_event(
        user=entry["user_id"][:20],
        op="Verification",
        algo="ML-DSA-65",
        result=result
    )
    return {
        "valid": valid,
        "signer_id": entry["user_id"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "integrity": "confirmed" if valid else "tampered",
    }


@router.get("/signature/{signature_id}/download")
async def download_signature(signature_id: str):
    """Downloads a signature file."""
    entry = SIGNATURES_DB.get(signature_id)
    if not entry:
        return PlainTextResponse("Not found", status_code=404)
    return PlainTextResponse(entry["hex"])
