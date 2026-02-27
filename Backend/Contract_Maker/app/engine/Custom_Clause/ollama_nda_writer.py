from __future__ import annotations

import subprocess
import json

OLLAMA_MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """
You are an Indian contract drafting assistant.

Draft a SINGLE NDA clause in formal legal English.
Rules:
- Civil liability only
- No criminal language
- No police, jail, FIR, punishment
- NDA context only
- Do NOT mention sections or cases
Return ONLY clause text.
"""

def generate_nda_clause(intent: str, user_input: str) -> str | None:
    if intent == "unknown":
        return None

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {
                "role": "user",
                "content": f"User requirement: {user_input}"
            }
        ],
        "stream": False
    }

    try:
        res = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=json.dumps(payload).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )

        if res.returncode != 0:
            return None

        text = res.stdout.decode().strip()
        return text if text else None

    except Exception:
        return None
