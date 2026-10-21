"""Tamper-evident audit log: each event's SHA-256 covers its content + the previous hash."""
import hashlib, json, datetime as dt
from sqlalchemy import select
from .db import AuditEvent, EvalSession

GENESIS = "0" * 64
FIELDS = ("idx", "ts", "subject", "action", "resource", "decision", "note", "prev_hash")

def digest(e) -> str:
    body = json.dumps({f: getattr(e, f) for f in FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()

def append(db, session_id, subject, action, resource, decision, note=""):
    # lock the session row so concurrent writers can't fork the chain
    db.execute(select(EvalSession).where(EvalSession.id == session_id).with_for_update())
    last = db.execute(select(AuditEvent).where(AuditEvent.session_id == session_id)
                      .order_by(AuditEvent.idx.desc()).limit(1)).scalar_one_or_none()
    e = AuditEvent(session_id=session_id, idx=(last.idx + 1) if last else 0,
                   ts=dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
                   subject=subject, action=action, resource=resource, decision=decision,
                   note=note, prev_hash=last.hash if last else GENESIS, hash="")
    e.hash = digest(e)
    db.add(e); db.flush()
    return e

def verify(db, session_id):
    """Returns (ok, first_broken_idx | None)."""
    prev = GENESIS
    rows = db.execute(select(AuditEvent).where(AuditEvent.session_id == session_id)
                      .order_by(AuditEvent.idx)).scalars().all()
    for e in rows:
        if e.prev_hash != prev or digest(e) != e.hash:
            return False, e.idx
        prev = e.hash
    return True, None
