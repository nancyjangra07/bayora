"""Client-LLM adapter (planned integration). Set LLM_API_URL to forward to a real endpoint."""
import os, httpx

def invoke(prompt: str) -> str:
    url = os.getenv("LLM_API_URL")
    if not url:
        return "I can't help with that request. (stub LLM: set LLM_API_URL to connect a real model)"
    r = httpx.post(url, json={"prompt": prompt}, timeout=30)
    r.raise_for_status()
    return r.json().get("output", "")
