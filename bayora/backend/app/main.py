import os, uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from . import audit, policy, sandbox, llm, risk
from .db import SessionLocal, EvalSession, AuditEvent, init_db

app = FastAPI(title="Bayora Control Plane")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def _startup(): init_db()

def get_db():
    with SessionLocal() as db:
        yield db

class ActionIn(BaseModel):
    subject: str   # red | blue | llm
    action: str    # invoke | read | write | connect
    resource: str  # llm | blue.state | blue.net | blue.rules | red.payloads | env.state
    payload: str = ""

def ev_out(e):
    return {k: getattr(e, k) for k in ("idx", "ts", "subject", "action", "resource", "decision", "note", "prev_hash", "hash")}

def need(db, sid):
    s = db.get(EvalSession, sid)
    if not s: raise HTTPException(404, "session not found")
    return s

@app.post("/sessions")
def create_session(db=Depends(get_db)):
    sid = uuid.uuid4().hex[:10]
    db.add(EvalSession(id=sid)); db.flush()
    envs = sandbox.provision(sid)
    audit.append(db, sid, "admin", "create", "session", "ALLOW", f"3 isolated envs provisioned ({sandbox.MODE})")
    db.commit()
    return {"id": sid, "environments": envs}

@app.post("/sessions/{sid}/actions")
def do_action(sid: str, a: ActionIn, db=Depends(get_db)):
    s = need(db, sid)
    d = policy.decide(a.subject, a.action, a.resource, s.red_quota_used)
    e = audit.append(db, sid, a.subject, a.action, a.resource, "ALLOW" if d.allowed else "DENY", d.reason)
    out = None
    if d.allowed and a.resource == "llm":
        if a.subject == "red": s.red_quota_used += 1
        out = llm.invoke(a.payload)
    db.commit()
    return {"decision": e.decision, "reason": d.reason, "output": out, "event": ev_out(e)}

@app.get("/sessions/{sid}/events")
def events(sid: str, db=Depends(get_db)):
    need(db, sid)
    rows = db.execute(select(AuditEvent).where(AuditEvent.session_id == sid).order_by(AuditEvent.idx)).scalars()
    return [ev_out(e) for e in rows]

@app.get("/sessions/{sid}/verify")
def verify(sid: str, db=Depends(get_db)):
    need(db, sid); ok, idx = audit.verify(db, sid)
    return {"intact": ok, "first_broken_event": idx}

@app.get("/sessions/{sid}/report")
def report(sid: str, db=Depends(get_db)):
    need(db, sid); return risk.report(db, sid)

@app.delete("/sessions/{sid}")
def close(sid: str, db=Depends(get_db)):
    s = need(db, sid); sandbox.teardown(sid); s.status = "closed"
    audit.append(db, sid, "admin", "destroy", "session", "ALLOW", "sandboxes torn down"); db.commit()
    return {"closed": sid}

@app.post("/dev/tamper/{sid}/{idx}")
def tamper(sid: str, idx: int, db=Depends(get_db)):
    """Demo only: mutates an entry so /verify fails. 404 unless ENABLE_TAMPER_DEMO=1."""
    if os.getenv("ENABLE_TAMPER_DEMO") != "1": raise HTTPException(404)
    e = db.execute(select(AuditEvent).where(AuditEvent.session_id == sid, AuditEvent.idx == idx)).scalar_one()
    e.decision = "ALLOW" if e.decision == "DENY" else "DENY"; db.commit()
    return {"tampered": idx}
