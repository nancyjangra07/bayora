import os
os.environ["ENABLE_TAMPER_DEMO"] = "1"
from fastapi.testclient import TestClient
from app.main import app

def test_flow():
    with TestClient(app) as c:
        sid = c.post("/sessions").json()["id"]
        act = lambda s, a, r: c.post(f"/sessions/{sid}/actions", json={"subject": s, "action": a, "resource": r, "payload": "hi"}).json()
        assert act("red", "invoke", "llm")["decision"] == "ALLOW"
        assert act("red", "read", "blue.state")["decision"] == "DENY"
        assert act("blue", "read", "red.payloads")["decision"] == "DENY"
        assert act("llm", "read", "env.state")["decision"] == "DENY"
        for _ in range(6): last = act("red", "invoke", "llm")
        assert last["decision"] == "DENY" and "quota" in last["reason"]
        assert c.get(f"/sessions/{sid}/verify").json()["intact"] is True
        c.post(f"/dev/tamper/{sid}/2")
        v = c.get(f"/sessions/{sid}/verify").json()
        assert v["intact"] is False and v["first_broken_event"] == 2
        assert c.get(f"/sessions/{sid}/report").json()["assessed_risk"] == "HIGH"
