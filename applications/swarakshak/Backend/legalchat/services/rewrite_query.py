import subprocess
import json

OLLAMA_MODEL = "llama3.1:8b"

# ==================================================
# SYSTEM PROMPTS
# ==================================================

SYSTEM_PROMPT_REWRITE = """
You are a legal query normalizer for Indian law research systems.

Your task is to rewrite the user's question into a neutral,
fact-focused, and search-optimized legal question suitable for
retrieving Indian statutes or Indian court judgments.

STRICT RULES:
- Do NOT answer the question.
- Do NOT add legal conclusions or opinions.
- Do NOT mention sections, articles, or case names.
- Do NOT change the intent of the question.
- Preserve the original legal issue.
- Use clear nouns and verbs commonly used in legal texts.
- If the question is already precise and searchable, return it unchanged.

Output ONLY the rewritten question in formal English.
No explanations. No extra text.
"""

SYSTEM_PROMPT_REFINE = """
You are a legal explanation simplifier.

Your task is to rewrite the given legal explanation in very simple,
clear, and user-friendly English so that a non-lawyer can understand it.

RULES:
- Do NOT add new legal reasoning.
- Do NOT change the conclusion or risk level.
- Do NOT cite new laws, sections, or cases.
- Do NOT give legal advice.
- Keep the meaning exactly the same.
- Avoid complex legal language.

Output ONLY the simplified explanation.
"""

# ==================================================
# INTERNAL HELPERS
# ==================================================

def _run_ollama(payload: dict) -> str:
    """
    Runs Ollama safely and returns text output.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=json.dumps(payload).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20
        )
        output = result.stdout.decode("utf-8", errors="ignore").strip()
        return output
    except Exception:
        return ""

# ==================================================
# QUERY REWRITE (BACKEND)
# ==================================================

def rewrite_query(user_query: str) -> str:
    """
    Rewrites a user query into a backend-searchable legal query.
    """

    if not user_query or len(user_query.strip()) < 5:
        return user_query

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_REWRITE},
            {"role": "user", "content": user_query}
        ],
        "stream": False
    }

    rewritten = _run_ollama(payload)

    # Fail-safe: never return empty or dangerous rewrite
    if not rewritten:
        return user_query

    # If LLM returns same text or garbage, keep original
    if len(rewritten.split()) < 4:
        return user_query

    return rewritten

# ==================================================
# ANALYSIS REFINEMENT (USER-FACING)
# ==================================================

def refine_analysis(text: str) -> str:
    """
    Simplifies legal explanation for end users.
    """

    if not text or len(text.strip()) < 10:
        return text

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_REFINE},
            {"role": "user", "content": text}
        ],
        "stream": False
    }

    refined = _run_ollama(payload)

    # Fail-safe
    if not refined:
        return text

    return refined
