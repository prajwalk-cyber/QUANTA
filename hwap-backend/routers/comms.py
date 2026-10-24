"""Comms router — real AES-256-GCM encrypt/decrypt with stored session state."""
from fastapi import APIRouter
from models.schemas import EncryptRequest, EncryptResponse, SendRequest, SendResponse, DecryptRequest, DecryptResponse
from crypto.symmetric import encrypt_gcm, decrypt_gcm
from routers import audit
import os
import uuid

router = APIRouter(prefix="/api")

# {session_id: {"key": bytes, "nonce": bytes, "ct": bytes, "plaintext": str}}
SESSIONS: dict[str, dict] = {}
# {delivery_id: session_id}
DELIVERIES: dict[str, str] = {}


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt_route(req: EncryptRequest):
    """Encrypts plaintext with a fresh session key using AES-256-GCM."""
    key = os.urandom(32)
    ct, nonce, _ = encrypt_gcm(key, req.plaintext.encode("utf-8"))
    SESSIONS[req.session_id] = {
        "key": key,
        "nonce": nonce,
        "ct": ct,
        "plaintext": req.plaintext,
    }
    audit.add_event(
        user="session",
        op="Encryption",
        algo="AES-256-GCM",
        result="Success"
    )
    return {"ciphertext_hex": ct.hex(), "nonce": nonce.hex()}


@router.post("/send", response_model=SendResponse)
async def send_route(req: SendRequest):
    """Sends the ciphertext — records delivery_id mapped to session."""
    delivery_id = str(uuid.uuid4())
    # Map delivery back to session so decrypt can look it up
    DELIVERIES[delivery_id] = req.session_id
    audit.add_event(
        user="session",
        op="Transmission",
        algo="AES-256-GCM",
        result="Delivered"
    )
    return {"delivery_id": delivery_id, "status": "sent"}


@router.post("/decrypt", response_model=DecryptResponse)
async def decrypt_route(req: DecryptRequest):
    """Decrypts ciphertext using the stored session key and nonce."""
    session_id = DELIVERIES.get(req.delivery_id, req.session_id)
    sess = SESSIONS.get(session_id)
    if not sess:
        return {"plaintext": "[Session not found]", "verified": False}
    try:
        plaintext_bytes, verified_gcm, _ = decrypt_gcm(sess["key"], sess["nonce"], sess["ct"])
        plaintext = plaintext_bytes.decode("utf-8")
        verified = True
    except Exception:
        plaintext = "[Decryption failed]"
        verified = False

    audit.add_event(
        user="session",
        op="Decryption",
        algo="AES-256-GCM",
        result="Success" if verified else "Failed"
    )
    return {"plaintext": plaintext, "verified": verified}
