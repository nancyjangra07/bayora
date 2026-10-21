"""Sandbox manager. Three roles, three internal-only networks => no route between sandboxes.
SANDBOX_MODE=docker launches hardened containers; 'simulated' (default) only records them."""
import os
ROLES = ("red", "llm", "blue")
MODE = os.getenv("SANDBOX_MODE", "simulated")
IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")

HARDENING = dict(
    read_only=True, cap_drop=["ALL"], security_opt=["no-new-privileges:true"],  # add seccomp=<profile.json> here
    mem_limit="256m", pids_limit=64, nano_cpus=500_000_000, user="65534:65534",
    tmpfs={"/tmp": "size=16m,noexec"},
)

def _client():
    import docker
    return docker.from_env()

def provision(session_id: str) -> dict:
    if MODE != "docker":
        return {r: {"mode": "simulated", "name": f"bayora-{session_id}-{r}"} for r in ROLES}
    c, out = _client(), {}
    for r in ROLES:
        name = f"bayora-{session_id}-{r}"
        net = c.networks.create(name, driver="bridge", internal=True, labels={"bayora": session_id})
        ct = c.containers.run(IMAGE, ["sleep", "infinity"], name=name, detach=True,
                              network=net.name, labels={"bayora": session_id, "role": r}, **HARDENING)
        out[r] = {"mode": "docker", "name": name, "id": ct.short_id}
    return out

def teardown(session_id: str):
    if MODE != "docker": return
    c = _client()
    for ct in c.containers.list(all=True, filters={"label": f"bayora={session_id}"}):
        ct.remove(force=True)
    for n in c.networks.list(filters={"label": f"bayora={session_id}"}):
        n.remove()
