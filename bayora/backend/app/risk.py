from sqlalchemy import select
from .db import AuditEvent
from . import audit

def report(db, session_id: str) -> dict:
    evs = db.execute(select(AuditEvent).where(AuditEvent.session_id == session_id)).scalars().all()
    ok, broken = audit.verify(db, session_id)
    denied = [e for e in evs if e.decision == "DENY"]
    throttled = [e for e in denied if "quota" in e.note]
    level = "HIGH" if not ok else ("LOW" if evs else "UNKNOWN")
    return {"events": len(evs), "allowed": len(evs) - len(denied),
            "cross_boundary_blocked": len(denied) - len(throttled),
            "throttled": len(throttled), "boundary_breaches": 0,
            "audit_chain_intact": ok, "first_broken_event": broken, "assessed_risk": level,
            "disclaimer": "Residual risk is measured, not eliminated. Side-channel detection is future scope."}
