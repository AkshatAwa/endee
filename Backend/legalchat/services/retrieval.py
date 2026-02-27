from __future__ import annotations

import faiss
import pickle
import json
import numpy as np
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Tuple, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
STORE_DIR = BASE_DIR / "faiss_store"
STATUTES_DIR = BASE_DIR / "data" / "statutes"

index = faiss.read_index(str(STORE_DIR / "index.faiss"))

with open(STORE_DIR / "metadata.pkl", "rb") as f:
    METADATA = pickle.load(f)

with open(STORE_DIR / "vectorizer.pkl", "rb") as f:
    VECTORIZER: TfidfVectorizer = pickle.load(f)

try:
    with open(STORE_DIR / "documents.pkl", "rb") as f:
        DOCUMENTS = pickle.load(f)
except Exception:
    DOCUMENTS = []

DECLARATORY_SECTIONS_ICA = {"11", "25", "27", "28", "30", "56"}

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

def _is_declaratory_ica(statute: str, section_no: Optional[str]) -> bool:
    if not section_no:
        return False
    s = statute.lower()
    return "indian contract act" in s and section_no in DECLARATORY_SECTIONS_ICA

def norm(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[']", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

SECTION_KEYWORDS = {
    "termination": 3,
    "retrench": 3,
    "notice": 3,
    "dismiss": 3,
    "discharge": 3,
    "procedure": 1,
    "authority": 1
}

def section_relevance_score(identifier: str) -> int:
    if not identifier:
        return 0
    s = identifier.lower()
    score = 0
    for k, v in SECTION_KEYWORDS.items():
        if k in s:
            score += v
    return score

def _keyword_overlap_score(query: str, doc_text: str) -> float:
    qw = set(re.findall(r"\w+", norm(query)))
    dw = set(re.findall(r"\w+", norm(doc_text)[:3000]))
    if not qw:
        return 0.0
    overlap = len(qw & dw) / len(qw)
    return min(overlap, 1.0)

def classify_domain(query: str) -> str:
    q = norm(query)
    if any(k in q for k in ["neither party", "indemnify", "confidential", "confidentiality", "arbitration", "governing law", "damages", "liability"]):
        # DOMAIN CORRECTION: If it looks like a question about legality, use contract_law.
        # If it looks like a clause text (checked by ask.py's looks_like_contract_clause), it will be handled there.
        # However, retrieve_for_contract uses this.
        # We'll default to contract_clause for compatibility, but allow contract_law if passed?
        # Actually, user wants "Use domain = contract_law" for legality questions.
        # Simple heuristic: if it contains "?" or "is " or "can " or "does ", it's likely a question.
        if "?" in q or any(w in q for w in ["is ", "can ", "does ", "what "]):
            return "contract_law"
        return "contract_clause"
    if any(k in q for k in ["usa", "uk", "california", "gdpr", "at will employment", "foreign law"]):
        return "foreign_jurisdiction"
    if any(k in q for k in ["jail", "arrest", "police", "criminal", "imprison"]):
        return "criminal_confusion"
    if any(k in q for k in ["employee", "employer", "salary", "termination", "resign", "non compete", "non-compete"]):
        return "employment_contract"
    if any(k in q for k in ["labour", "workman", "retrench"]):
        return "labour_law"
    return "general"

BASE_CASES = {
    "confidentiality": {
        "status": "legal_with_conditions",
        "risk_level": "medium",
        "verdict": "DEPENDS",
        "analysis": "Confidentiality obligations are generally enforceable under Indian contract law, subject to reasonableness and public policy.",
        "law_basis": "Indian Contract Act, 1872"
    },
    "indemnity": {
        "status": "legal",
        "risk_level": "medium",
        "verdict": "LEGAL",
        "analysis": "Indemnity clauses are governed by Sections 124–125 of the Indian Contract Act.",
        "law_basis": "Indian Contract Act, Sections 124–125"
    },
    "penalty": {
        "status": "legal_with_conditions",
        "risk_level": "high",
        "verdict": "DEPENDS",
        "analysis": "Penalty clauses are subject to scrutiny under Section 74 of the Indian Contract Act.",
        "law_basis": "Indian Contract Act, Section 74"
    },
    "non_compete_employment": {
        "status": "illegal",
        "risk_level": "high",
        "verdict": "ILLEGAL",
        "analysis": "Post-employment non-compete clauses are void under Indian law.",
        "law_basis": "Indian Contract Act, Section 27"
    },
    "arbitration": {
        "status": "legal",
        "risk_level": "low",
        "verdict": "LEGAL",
        "analysis": "Arbitration agreements are enforceable under Indian law.",
        "law_basis": "Arbitration & Conciliation Act, 1996"
    },
    "consideration": {
        "status": "illegal",
        "risk_level": "high",
        "verdict": "ILLEGAL",
        "analysis": "An agreement without consideration is void under Indian law, save for the limited exceptions in Section 25.",
        "law_basis": "Indian Contract Act, Section 25"
    }
}

def resolve_base_case(query: str, domain: str) -> Optional[Dict]:
    q = norm(query)
    if "consideration" in q and ("without" in q or "no " in q or "absence" in q):
        return BASE_CASES["consideration"]
    if domain == "contract_clause" or domain == "contract_law":
        if "confidential" in q:
            return BASE_CASES["confidentiality"]
        if "indemnity" in q:
            return BASE_CASES["indemnity"]
        if "penalty" in q or "liquidated damages" in q:
            return BASE_CASES["penalty"]
        if "arbitration" in q:
            return BASE_CASES["arbitration"]
    if domain == "employment_contract" and ("non compete" in q or "noncompete" in q):
        return BASE_CASES["non_compete_employment"]
    return None

STATUTE_PRIORITY = {
    "industrial disputes act": 3,
    "standing orders act": 3,
    "shops and establishments act": 2,
    "indian contract act": 1,
}

def vectorize(q: str) -> np.ndarray:
    return VECTORIZER.transform([q]).toarray().astype(np.float32)

def faiss_rank_with_scores(query: str, indices: List[int], k: int = 20) -> List[Tuple[int, float]]:
    if not indices:
        return []
    vec = vectorize(query)
    sub_vectors = np.array([index.reconstruct(i) for i in indices], dtype=np.float32)
    if sub_vectors.ndim != 2 or sub_vectors.shape[0] == 0:
        return []
    sub_index = faiss.IndexFlatL2(sub_vectors.shape[1])
    sub_index.add(sub_vectors)
    distances, ids = sub_index.search(vec, min(k, len(sub_vectors)))
    paired = list(zip(distances[0], ids[0]))
    paired.sort(key=lambda x: (x[0], indices[x[1]]))
    return [(indices[i], float(d)) for d, i in paired]

LEGAL_DIMENSIONS = {
    "procedural_safeguards": ["without notice", "no notice", "notice period", "prior notice", "due process", "procedure before termination"],
    "disciplinary_action": ["misconduct", "disciplinary", "inquiry", "charge sheet"],
    "post_termination_rights": ["compensation", "retrenchment benefits", "reinstatement", "back wages"]
}

DIMENSION_PATTERNS = {
    "procedural_safeguards": ["notice", "retrench", "prior permission", "approval"],
    "disciplinary_action": ["misconduct", "disciplinary"],
    "post_termination_rights": ["compensation", "reinstatement", "benefit"]
}

def detect_dimension(query: str) -> Optional[str]:
    q = norm(query)
    for dim, keywords in LEGAL_DIMENSIONS.items():
        if any(k in q for k in keywords):
            return dim
    return None

ALLOWED_STATUTES = {
    "contract_clause": ["indian contract act"],
    "contract_law": ["indian contract act"],
    "employment_contract": ["indian contract act", "industrial disputes act"],
    "labour_law": ["industrial disputes act"],
}

def get_candidate_indices(domain: str) -> List[int]:
    allowed = ALLOWED_STATUTES.get(domain, [])
    indices = []
    for i, m in enumerate(METADATA):
        statute = (m.get("statute") or "").lower()
        if any(a in statute for a in allowed):
            indices.append(i)
    return indices

def _semantic_from_distance(d: float) -> float:
    return 1.0 / (1.0 + max(0.0, d))

def filter_citations(domain: str, ranked_with_dist: List[Tuple[int, float]], query: str) -> List[Dict]:
    seen = set()
    scored = []
    for idx, dist in ranked_with_dist:
        m = METADATA[idx]
        key = (m.get("type"), m.get("identifier"))
        if key in seen:
            continue
        seen.add(key)
        statute = (m.get("statute") or "").lower()
        section_no = _extract_section_no(m.get("identifier", ""))
        if m.get("type") == "statute" and not _statute_section_valid(statute, section_no):
            continue
        statute_priority = STATUTE_PRIORITY.get(next((k for k in STATUTE_PRIORITY if k in statute), ""), 0)
        kw_relevance = section_relevance_score(m.get("identifier", ""))
        semantic = _semantic_from_distance(dist)
        doc_text = DOCUMENTS[idx] if idx < len(DOCUMENTS) else f"{m.get('statute','')} {m.get('identifier','')}"
        keyword_overlap = _keyword_overlap_score(query, doc_text)
        relevance_score = (semantic + keyword_overlap) / 2.0
        validity_score = 1.0 if (m.get("type") != "statute" or _statute_section_valid(statute, section_no)) else 0.0
        is_declaratory = m.get("type") == "statute" and _is_declaratory_ica(statute, section_no)
        total_score = statute_priority * 10 + kw_relevance + relevance_score
        scored.append((total_score, {
            "type": m["type"],
            "identifier": m.get("identifier"),
            "statute": m.get("statute"),
            "source": m.get("source"),
            "is_declaratory": is_declaratory,
            "relevance_score": round(relevance_score, 4),
            "validity_score": validity_score
        }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:6]]

def infer_risk_level(domain: str, citations: list) -> str:
    if not citations:
        return "unknown"
    statutes = [(c.get("statute") or "").lower() for c in citations]
    if any("industrial disputes act" in s for s in statutes):
        return "medium"
    if any(k in s for s in statutes for k in ["penal", "ipc", "crpc"]):
        return "high"
    if domain == "general":
        return "low"
    return "medium"

def retrieve_for_contract(system_query: str) -> Dict:
    domain = classify_domain(system_query)
    if domain == "criminal_confusion":
        return {"status": "refused", "domain": domain, "reason": "Private contracts cannot impose criminal liability", "citations": [], "verdict": "UNKNOWN"}
    if domain == "foreign_jurisdiction":
        return {"status": "refused", "domain": domain, "reason": "Foreign law is outside the scope of this system", "citations": [], "verdict": "UNKNOWN"}
    candidate_indices = get_candidate_indices(domain)
    if not candidate_indices:
        return {"status": "no_authoritative_source", "domain": domain, "reason": "Query is too vague to map to a specific Indian statute", "citations": [], "verdict": "UNKNOWN"}
    ranked_with_dist = faiss_rank_with_scores(system_query, candidate_indices)
    citations = filter_citations(domain, ranked_with_dist, system_query)
    base = resolve_base_case(system_query, domain)
    if base:
        return {
            "status": base["status"],
            "domain": domain,
            "risk_level": base["risk_level"],
            "verdict": base["verdict"],
            "analysis": [base["analysis"]],
            "law_basis": base["law_basis"],
            "citations": citations
        }
    if citations:
        inferred_risk = infer_risk_level(domain, citations)
        return {
            "status": "ok",
            "domain": domain,
            "risk_level": inferred_risk,
            "verdict": "DEPENDS",
            "citations": citations
        }
    return {"status": "no_authoritative_source", "domain": domain, "reason": "No relevant Indian statute applicable", "citations": [], "verdict": "UNKNOWN"}
