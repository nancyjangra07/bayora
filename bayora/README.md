# Bayora — Secure Adversarial AI Testing Infrastructure
*Attack the AI. Defend the AI. Trust the Evaluation.* · Team Jab We Code · Hack in Hills '26 · PS 04

Red team, Blue team and the client LLM each get an isolated sandbox. A control plane enforces a default-deny
capability policy, governs resources, and writes every decision to a SHA-256 hash-chained audit log that a
risk engine turns into a security report.

```
Next.js UI ──► FastAPI control plane ──► Policy engine (capability ACL + quota)
                     │                ├─► Sandbox manager (Docker: 3 internal networks, cap_drop ALL,
                     │                │    read-only fs, no-new-privileges, mem/pids/cpu limits)
                     │                ├─► Audit engine (hash chain, PostgreSQL)
                     │                └─► Risk engine ──► report
                     └─► LLM adapter (stub; set LLM_API_URL for a real model — "Planned" in the deck)
```

## Run
```bash
docker compose up --build        # UI :3000, API :8000 (docs at :8000/docs)
SANDBOX_MODE=docker docker compose up --build   # launch real hardened containers (mounts docker.sock)
ENABLE_TAMPER_DEMO=1 ...         # enable the demo tamper endpoint (add to backend env in compose)
```
Local dev: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload` (SQLite fallback),
then `cd frontend && npm install && npm run dev`. Backend test: `python -m pytest backend/test_api.py`.

## Demo scenario (slide 7)
Create session → Red submits a test → Red reads Blue state (BLOCKED) → Red opens socket to Blue (BLOCKED) →
Blue deploys rule → Verify chain → Generate report.

## Honest limits
Sandboxes run only a placeholder process; actions are mediated by the control plane rather than executed inside them.
A custom seccomp profile is a TODO (marked in `sandbox.py`). Mounting `docker.sock` is for local demos only.
The tamper endpoint is for demos. Residual risk is measured, not eliminated; side-channel detection is future scope.
