"""Default-deny capability ACL + resource governance."""
from dataclasses import dataclass

# (subject, action, resource) -> allowed.  Anything not listed is DENIED.
CAPABILITIES = {
    ("red",   "invoke", "llm"),
    ("blue",  "invoke", "llm"),
    ("blue",  "write",  "blue.rules"),
    ("admin", "create", "session"),
}
RED_LLM_QUOTA = 5

@dataclass
class Decision:
    allowed: bool
    reason: str

def decide(subject: str, action: str, resource: str, red_quota_used: int = 0) -> Decision:
    if (subject, action, resource) not in CAPABILITIES:
        return Decision(False, "no capability granted (default deny)")
    if subject == "red" and resource == "llm" and red_quota_used >= RED_LLM_QUOTA:
        return Decision(False, f"resource governance: quota {RED_LLM_QUOTA} exceeded")
    return Decision(True, "capability granted")
