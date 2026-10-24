"""Audit router — shared in-memory event log."""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/api")

# Shared in-memory audit log (list of dicts, newest first)
AUDIT_LOG: list[dict] = []


def add_event(user: str, op: str, algo: str, result: str) -> None:
    """Prepend a new audit event. Called by all other routers."""
    AUDIT_LOG.insert(0, {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "op": op,
        "algo": algo,
        "result": result,
    })
    # Keep log from growing unbounded in long-running sessions
    if len(AUDIT_LOG) > 500:
        AUDIT_LOG.pop()


@router.get("/audit")
async def get_audit(search: str = "", filter: str = "all"):
    """Returns the real-time audit log, optionally filtered."""
    rows = AUDIT_LOG
    if filter and filter != "all":
        rows = [e for e in rows if e["op"] == filter]
    if search:
        s = search.lower()
        rows = [e for e in rows if s in e["user"].lower() or s in e["op"].lower()]
    return rows
