"""System routers."""
from fastapi import APIRouter
from hndlr import compute_score
from state import get_active_tier
import time

router = APIRouter(prefix="/api")
START_TIME = time.time()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "active_tier": get_active_tier(),
        "liboqs_version": "0.10.0",
        "uptime_s": round(time.time() - START_TIME, 2)
    }

@router.get("/score")
async def score():
    return compute_score(get_active_tier())
