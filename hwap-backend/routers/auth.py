"""Auth and Keys routers."""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
import time
import os
from models.schemas import UserRegister, UserResponse, GenerateKeysRequest, GenerateKeysResponse
from keystore import store_private_key
from routers import audit

try:
    import oqs
    if hasattr(oqs, 'KeyEncapsulation') and hasattr(oqs, 'Signature'):
        OQS_AVAILABLE = True
    else:
        OQS_AVAILABLE = False
except ImportError:
    OQS_AVAILABLE = False

auth_router = APIRouter(prefix="/api")
keys_router = APIRouter(prefix="/api/generate-keys")

# ── In-memory registries (visible via GET endpoints) ──────────────────────
USER_REGISTRY: list[dict] = []          # all registered users
PUBLIC_KEY_REGISTRY: list[dict] = []    # all generated public keys


@auth_router.post("/register", response_model=UserResponse)
async def register(req: UserRegister):
    """Registers a user."""
    user_id = str(uuid.uuid4())
    display_name = f"{req.name} — {user_id[:8].upper()}"
    created_at = datetime.utcnow().isoformat()

    # Store in the registry so GET /api/users can return it
    USER_REGISTRY.append({
        "user_id": user_id,
        "name": req.name,
        "display_name": display_name,
        "created_at": created_at,
    })

    audit.add_event(
        user=display_name,
        op="Registration",
        algo="—",
        result="Success"
    )
    return {"user_id": user_id, "created_at": created_at}


@auth_router.get("/users")
async def list_users():
    """Returns all registered users (visible in Swagger UI)."""
    return {
        "count": len(USER_REGISTRY),
        "users": USER_REGISTRY,
    }


@auth_router.get("/users/{user_id}/keys")
async def get_user_keys(user_id: str):
    """Returns all public keys generated for a specific user."""
    user_keys = [k for k in PUBLIC_KEY_REGISTRY if k["user_id"] == user_id]
    if not user_keys:
        raise HTTPException(status_code=404, detail=f"No keys found for user {user_id}")
    return {
        "user_id": user_id,
        "count": len(user_keys),
        "keys": user_keys,
    }


@auth_router.get("/keys")
async def list_all_keys():
    """Returns all generated public keys across all users."""
    return {
        "count": len(PUBLIC_KEY_REGISTRY),
        "keys": PUBLIC_KEY_REGISTRY,
    }


@keys_router.post("/kem", response_model=GenerateKeysResponse)
async def generate_kem_keys(req: GenerateKeysRequest):
    """Generates KEM keypair."""
    start = time.perf_counter()
    if OQS_AVAILABLE:
        with oqs.KeyEncapsulation('Kyber768') as kem:
            pub = kem.generate_keypair()
            priv = kem.export_secret_key()
    else:
        pub = os.urandom(1184)
        priv = os.urandom(32)

    pub_hex = pub.hex()
    store_private_key(req.user_id, "ML-KEM-768", priv)
    keygen_ms = round((time.perf_counter() - start) * 1000, 2)

    # Store in public key registry
    PUBLIC_KEY_REGISTRY.append({
        "user_id": req.user_id,
        "algorithm": "ML-KEM-768",
        "public_key_hex": pub_hex,
        "key_size_bytes": len(pub),
        "keygen_ms": keygen_ms,
        "generated_at": datetime.utcnow().isoformat(),
    })

    audit.add_event(
        user=req.user_id[:20],
        op="Key Generation",
        algo="ML-KEM-768",
        result="Success"
    )
    return {
        "public_key_hex": pub_hex,
        "algorithm": "ML-KEM-768",
        "keygen_ms": keygen_ms
    }

@keys_router.post("/dsa", response_model=GenerateKeysResponse)
async def generate_dsa_keys(req: GenerateKeysRequest):
    """Generates DSA keypair."""
    start = time.perf_counter()
    if OQS_AVAILABLE:
        with oqs.Signature('Dilithium3') as sig:
            pub = sig.generate_keypair()
            priv = sig.export_secret_key()
    else:
        pub = os.urandom(1952)
        priv = os.urandom(32)

    pub_hex = pub.hex()
    store_private_key(req.user_id, "ML-DSA-65", priv)
    keygen_ms = round((time.perf_counter() - start) * 1000, 2)

    # Store in public key registry
    PUBLIC_KEY_REGISTRY.append({
        "user_id": req.user_id,
        "algorithm": "ML-DSA-65",
        "public_key_hex": pub_hex,
        "key_size_bytes": len(pub),
        "keygen_ms": keygen_ms,
        "generated_at": datetime.utcnow().isoformat(),
    })

    audit.add_event(
        user=req.user_id[:20],
        op="Key Generation",
        algo="ML-DSA-65",
        result="Success"
    )
    return {
        "public_key_hex": pub_hex,
        "algorithm": "ML-DSA-65",
        "keygen_ms": keygen_ms
    }
