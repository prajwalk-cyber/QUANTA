"""Handshake router."""
from fastapi import APIRouter
from models.schemas import HandshakeRequest, HandshakeResponse, SwitchTierRequest, SwitchTierResponse
from crypto.kem import run_hybrid_handshake
from crypto.shst import generate_shst_token
from state import set_active_tier
from routers import audit
import time
import uuid

router = APIRouter(prefix="/api")

@router.post("/handshake", response_model=HandshakeResponse)
async def handshake(req: HandshakeRequest):
    """Performs hybrid handshake."""
    res = run_hybrid_handshake(req.tier)
    algo = "ML-KEM-768 + X25519" if req.tier == 1 else "ML-KEM-768" if req.tier == 2 else "X25519" if req.tier == 3 else "X25519"
    sec_lvl = "Post-Quantum" if req.tier in (1, 2) else "Classical"
    tier_name = ["Tier 1 Hybrid", "Tier 2 KEM-only", "Tier 3 Sig-only", "Tier 4 Classical"][req.tier - 1]

    audit.add_event(
        user="session",
        op="Handshake",
        algo=tier_name,
        result="Completed"
    )

    return {
        "session_id": str(uuid.uuid4()),
        "algorithm": algo,
        "tier": req.tier,
        "K_hybrid_hex": res["K_hybrid_hex"],
        "shst_token": generate_shst_token(),
        "shst_expires_at": int(time.time()) + 3600,
        "overhead_saving_pct": 83,
        "timing": res["timing"],
        "security_level": sec_lvl
    }

@router.post("/switch-tier", response_model=SwitchTierResponse)
async def switch_tier(req: SwitchTierRequest):
    """Switches the active tier."""
    set_active_tier(req.tier)
    algo_set = "ML-KEM-768 + X25519, ML-DSA-65"
    if req.tier == 2: algo_set = "ML-KEM-768, ECDSA"
    if req.tier == 3: algo_set = "X25519, ML-DSA-65"
    if req.tier == 4: algo_set = "X25519, ECDSA"
    return {
        "active_tier": req.tier,
        "algorithm_set": algo_set,
        "message": f"Switched to Tier {req.tier}"
    }
