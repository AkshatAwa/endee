from __future__ import annotations

import json
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
STATUTES_DIR = BASE_DIR / "data" / "statutes"

ENDEE_BASE_URL = "http://localhost:8080"
INDEX_NAME = "legal_index"

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "mxbai-embed-large"

# -----------------------------
# STATUTE REGISTRY
# -----------------------------
def _load_statute_registry() -> Dict[str, set]:
    registry = {}
    if not STATUTES_DIR.exists():
        return registry
    for p in STATUTES_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            name = (data.get("name") or "").lower()
            sections = data.get("sections") or {}
            registry[name] = set(str(k) for k in sections.keys())
        except Exception:
            pass
    return registry

STATUTE_REGISTRY = _load_statute_registry()

# -----------------------------
# LOCAL EMBEDDING (OLLAMA)
# -----------------------------
def get_embedding(text: str) -> List[float]:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": EMBED_MODEL,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        raise RuntimeError(f"Ollama embedding failed: {str(e)}")
# -----------------------------
# ENDEE SEARCH
# -----------------------------
def endee_search(query: str, top_k: int = 20):
    try:
        embedding = get_embedding(query)

        response = requests.post(
            f"{ENDEE_BASE_URL}/api/v1/vector/search",
            json={
                "index_name": INDEX_NAME,
                "vector": embedding,
                "top_k": top_k
            },
            timeout=30
        )

        response.raise_for_status()

        results = response.json().get("results", [])

        ranked = []
        for r in results:
            metadata = r.get("metadata", {})
            distance = r.get("distance", 0.0)
            ranked.append((metadata, float(distance)))

        return ranked

    except Exception as e:
        raise RuntimeError(f"Endee search failed: {str(e)}") ranked

# -----------------------------
# UTILITIES
# -----------------------------
DECLARATORY_SECTIONS_ICA = {"11", "25", "27", "28", "30", "56"}

def norm(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[']", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _extract_section_no(identifier: str) -> Optional[str]:
    if not identifier:
        return None
    m = re.search(r"section\s+(\d+[a-z]?)", identifier.lower())
    return m.group(1) if m else None

def _statute_section_valid(statute: str, section_no: Optional[str]) -> bool:
    if not statute or not section_no:
        return False
    s = statute.lower()
    for reg_name, sections in STATUTE_REGISTRY.items():
        if reg_name in s:
            return section_no in sections
    return False

def _semantic_from_distance(d: float) -> float:
    return 1.0 / (1.0 + max(0.0, d))

# -----------------------------
# DOMAIN CLASSIFICATION
# -----------------------------
def classify_domain(query: str) -> str:
    q = norm(query)

    if any(k in q for k in ["confidential", "indemnify", "arbitration", "liability"]):
        return "contract_law"

    if any(k in q for k in ["employee", "employer", "salary", "termination"]):
        return "employment_contract"

    if any(k in q for k in ["labour", "retrench"]):
        return "labour_law"

    if any(k in q for k in ["jail", "arrest", "criminal"]):
        return "criminal_confusion"

    return "general"

# -----------------------------
# FILTER CITATIONS
# -----------------------------
def filter_citations(domain: str, ranked_with_dist) -> List[Dict]:
    scored = []

    for metadata, dist in ranked_with_dist:
        statute = (metadata.get("statute") or "").lower()
        identifier = metadata.get("identifier")
        section_no = _extract_section_no(identifier)

        if metadata.get("type") == "statute":
            if not _statute_section_valid(statute, section_no):
                continue

        semantic_score = _semantic_from_distance(dist)

        scored.append((semantic_score, {
            "type": metadata.get("type"),
            "identifier": identifier,
            "statute": metadata.get("statute"),
            "source": metadata.get("source"),
            "relevance_score": round(semantic_score, 4)
        }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:6]]

# -----------------------------
# MAIN ENTRY
# -----------------------------
def retrieve_for_contract(system_query: str) -> Dict:
    domain = classify_domain(system_query)

    if domain == "criminal_confusion":
        return {
            "status": "refused",
            "reason": "Private contracts cannot impose criminal liability",
            "verdict": "UNKNOWN"
        }

    ranked = endee_search(system_query, top_k=20)
    citations = filter_citations(domain, ranked)

    if citations:
        return {
            "status": "ok",
            "domain": domain,
            "verdict": "DEPENDS",
            "citations": citations
        }

    return {
        "status": "no_authoritative_source",
        "verdict": "UNKNOWN",
        "citations": []
    }
