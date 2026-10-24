"""Pydantic schemas with NoPrivateKeyMixin."""
from pydantic import BaseModel
from typing import Dict

class NoPrivateKeyMixin(BaseModel):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for field_name in cls.model_fields.keys():
            if "private" in field_name.lower() or "secret_key" in field_name.lower():
                raise ValueError(f"Field '{field_name}' in {cls.__name__} violates NoPrivateKeyMixin rules")

class UserRegister(BaseModel):
    name: str
    email: str
    organization: str

class UserResponse(NoPrivateKeyMixin):
    user_id: str
    created_at: str

class GenerateKeysRequest(BaseModel):
    user_id: str

class GenerateKeysResponse(NoPrivateKeyMixin):
    public_key_hex: str
    algorithm: str
    keygen_ms: float

class HandshakeRequest(BaseModel):
    tier: int

class HandshakeResponse(NoPrivateKeyMixin):
    session_id: str
    algorithm: str
    tier: int
    K_hybrid_hex: str
    shst_token: str
    shst_expires_at: int
    overhead_saving_pct: int = 83
    timing: Dict[str, float]
    security_level: str

class SwitchTierRequest(BaseModel):
    tier: int

class SwitchTierResponse(NoPrivateKeyMixin):
    active_tier: int
    algorithm_set: str
    message: str

class EncryptRequest(BaseModel):
    session_id: str
    plaintext: str

class EncryptResponse(NoPrivateKeyMixin):
    ciphertext_hex: str
    nonce: str

class SendRequest(BaseModel):
    session_id: str
    ciphertext_hex: str

class SendResponse(NoPrivateKeyMixin):
    delivery_id: str
    status: str

class DecryptRequest(BaseModel):
    session_id: str
    delivery_id: str

class DecryptResponse(NoPrivateKeyMixin):
    plaintext: str
    verified: bool

class SignRequest(BaseModel):
    user_id: str
    message: str

class SignResponse(NoPrivateKeyMixin):
    signature_id: str
    signature_hex: str
    algorithm: str
    sig_size_bytes: int
    sign_latency_ms: float

class VerifyRequest(BaseModel):
    signature_id: str
    message: str
    public_key_hex: str

class VerifyResponse(NoPrivateKeyMixin):
    valid: bool
    signer_id: str
    timestamp: str
    integrity: str

class HealthResponse(NoPrivateKeyMixin):
    status: str
    active_tier: int
    liboqs_version: str
    uptime_s: float
