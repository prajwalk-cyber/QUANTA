"""Global state for active tier and session store."""
from typing import Dict, Any

ACTIVE_TIER: int = 1

def get_active_tier() -> int:
    return ACTIVE_TIER

def set_active_tier(tier: int) -> None:
    global ACTIVE_TIER
    ACTIVE_TIER = tier
