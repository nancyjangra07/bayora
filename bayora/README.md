# Bayora: Secure Adversarial AI Testing Infrastructure

*Attack the AI. Defend the AI. Trust the Evaluation.*

**Team Jab We Code** · Hack in Hills '26 · PS 04: Secure Adversarial & Safety Testing Infrastructure

Bayora gives a Red team, a Blue team and the client LLM each their own isolated sandbox. A control plane enforces a
default-deny capability policy, throttles abusive usage, and writes every decision to a SHA-256 hash-chained audit log.
A risk engine turns that log into a security report, so the evaluation itself can be trusted.

## The problem

Red teams attack an AI system while Blue teams defend it, but both usually work in the same environment. That risks
data leakage between teams, an attacker interfering with the defence, no trustworthy record of what happened, and
results nobody can verify. Bayora separates the three parties and makes every action accountable.

## Features

| Feature | How it works here |
|---|---|
| Isolated sandboxes | Red, LLM and Blue each get their own environment on separate internal-only networks, so there is no route between them |
| Policy enforcement | Default-deny capability table in `backend/app/policy.py`; anything not explicitly allowed is blocked |
| Resource governance | Red is limited to 5 LLM calls per session; later calls are throttled |
| Tamper-evident audit log | Each event stores the SHA-256 hash of its content plus the previous event's hash; editing any entry breaks the chain |
| Risk report | Counts allowed actions, blocked cross-boundary attempts, throttled requests and audit integrity |

## Architecture

```
Next.js UI ──► FastAPI control plane ──► Policy engine (capability ACL + quota)
                     │                ├─► Sandbox manager (3 internal networks; in docker mode:
                     │                │    cap_drop ALL, read-only fs, no-new-privileges, mem/pids/cpu limits)
                     │                ├─► Audit engine (SHA-256 hash chain in PostgreSQL)
                     │                └─► Risk engine ──► security report
                     └─► LLM adapter (stub; set LLM_API_URL to connect a real model)
```

## Tech stack

- **Frontend:** Next.js 14, React 18, TypeScript
- **Backend:** FastAPI, SQLAlchemy, Python 3.12
- **Database:** PostgreSQL 16 (SQLite fallback for local development)
- **Isolation:** Docker (optional real-container mode)

## Project structure

```
backend/
  app/
    main.py       API routes
    policy.py     default-deny capability ACL + quota
    audit.py      hash-chained audit log + verification
    sandbox.py    sandbox manager (simulated or Docker)
    risk.py       security report
    llm.py        client-LLM adapter (stub)
    db.py         database models
  test_api.py     end-to-end API test
frontend/
  app/page.tsx    single-page UI
  lib/api.ts      API client
docker-compose.yml
```

## Run with Docker (recommended)

**Requirements:** [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
On Windows, Docker Desktop needs WSL 2 and the Virtual Machine Platform feature (use the *All-users* installer,
or run `wsl --install` in an administrator PowerShell and restart).

From the folder that contains `docker-compose.yml`:

```bash
docker compose up --build
```

The first build takes a few minutes. Then open:

- **App:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

Keep the terminal open while using the app. To stop: press `Ctrl+C`, then run `docker compose down`.
Next time, `docker compose up` is enough (add `--build` only after code changes).

### Real sandbox containers (optional)

By default sandboxes are simulated: they are recorded and governed but not launched. To launch real hardened
containers:

```bash
SANDBOX_MODE=docker docker compose up --build
```

On Windows PowerShell:

```powershell
$env:SANDBOX_MODE="docker"; docker compose up --build
```

This mounts `docker.sock` into the backend, so use it for local demos only.

## Run without Docker

You need Python 3.11+ and Node.js 18+. Use two terminals.

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
$env:ENABLE_TAMPER_DEMO="1"     # Mac/Linux: export ENABLE_TAMPER_DEMO=1
uvicorn app.main:app --reload
```

This uses a local SQLite file, so PostgreSQL is not needed. If `psycopg2-binary` fails to install, remove it from
`requirements.txt`; it is only needed for PostgreSQL.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Demo walkthrough

1. Click **Create session**. Three isolated environments are provisioned and event #0 is logged.
2. Click **Submit controlled test** (Red). The LLM refuses, and the action is **ALLOWED**.
3. Click **Read Blue state** and **Socket → Blue** (Red). Both are **BLOCKED**.
4. Click **Deploy defensive rule** (Blue). **ALLOWED**.
5. Click **Read Red payloads** (Blue) and **LLM reads env state** (LLM). Both are **BLOCKED**.
6. Click **Verify chain**. It reports `chain intact`.
7. Click **Tamper with an entry**, then **Verify chain** again. It reports `broken`, and the edited entry is highlighted.
8. Click **Generate report** to see the risk summary.

To see resource governance, click **Submit controlled test** six times in one session; the sixth call is throttled.
For a clean low-risk report, create a fresh session and skip the tamper step.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/sessions` | Create a session and provision sandboxes |
| POST | `/sessions/{id}/actions` | Submit an action; the policy engine decides and the audit log records it |
| GET | `/sessions/{id}/events` | List audit events |
| GET | `/sessions/{id}/verify` | Verify the hash chain |
| GET | `/sessions/{id}/report` | Generate the risk report |
| DELETE | `/sessions/{id}` | Close the session and tear down sandboxes |
| POST | `/dev/tamper/{id}/{idx}` | Demo only: edit an entry (404 unless `ENABLE_TAMPER_DEMO=1`) |

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite file | Database connection (set to PostgreSQL in `docker-compose.yml`) |
| `SANDBOX_MODE` | `simulated` | `docker` launches real hardened containers |
| `LLM_API_URL` | unset | Endpoint for a real model; unset uses a stub that returns a refusal |
| `ENABLE_TAMPER_DEMO` | `1` in compose | Enables the demo tamper endpoint |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Where the frontend finds the API |

## Tests

```bash
cd backend
python -m pytest test_api.py
```

## Troubleshooting

- **`localhost refused to connect`:** the containers are not running. Run `docker compose ps`, or start them again with
  `docker compose up`. Do not open `0.0.0.0` in a browser; use `localhost`.
- **`unexpected EOF` while booting buildkit:** Docker's download was interrupted. Retry, turn off any VPN, or run
  `docker pull moby/buildkit:buildx-stable-1` first.
- **`cannot find path ... backend`:** you are one folder too high or low. Run `dir` (Windows) or `ls` and check you can see
  `docker-compose.yml`.
- **Warning about `next start` and `output: standalone`:** harmless; the server still starts.
- **`frontend` shows as a 404 on GitHub:** a stray `.git` folder inside `frontend` makes Git treat it as a separate
  repository. Run `git rm --cached frontend`, delete `frontend/.git`, then `git add .` and commit again.

## Known limitations

- Sandboxes run only a placeholder process. Actions are decided and logged by the control plane, not executed inside them.
- No custom seccomp profile yet (marked as a TODO in `sandbox.py`).
- The client LLM is a stub unless `LLM_API_URL` is set.
- The tamper endpoint is for demos only; remove it for any real deployment.
- Mounting `docker.sock` (real-container mode) gives the backend broad control of the host Docker; do not use it outside local demos.
- Bayora measures residual risk, it does not eliminate it. Side-channel detection is future scope.

## Roadmap

Real LLM integration, per-session sandbox execution, multi-tenant organisations, a live monitoring dashboard,
custom seccomp profiles, and exportable signed audit reports.