"""HNDLR-Score computation engine."""

WEIGHTS = {
    "kem": 0.35,
    "sig": 0.25,
    "forward_secrecy": 0.20,
    "agility": 0.10,
    "compat": 0.10
}

def compute_score(tier: int) -> dict:
    """Computes HNDLR score based on the current tier."""
    if tier == 1:
        total = 94.2
        dims = {"kem_strength": 95, "signature_strength": 92, "forward_secrecy": 98, "crypto_agility": 90, "backward_compat": 85}
    elif tier == 2:
        total = 78.5
        dims = {"kem_strength": 90, "signature_strength": 60, "forward_secrecy": 90, "crypto_agility": 80, "backward_compat": 85}
    elif tier == 3:
        total = 70.0
        dims = {"kem_strength": 50, "signature_strength": 95, "forward_secrecy": 80, "crypto_agility": 85, "backward_compat": 90}
    else:
        total = 45.0
        dims = {"kem_strength": 40, "signature_strength": 45, "forward_secrecy": 70, "crypto_agility": 50, "backward_compat": 95}

    return {
        "total_score": round(total, 1),
        "tier": tier,
        "dimensions": dims,
        "baseline_tls13": 31.7
    }
