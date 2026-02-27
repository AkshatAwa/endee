import uuid
import datetime

from Backend.legalchat.services.rewrite_query import rewrite_query, refine_analysis
from Backend.legalchat.services.retrieval import retrieve_for_contract, classify_domain, resolve_base_case
from Backend.legalchat.services.analysis_generator import generate_analysis

# 🔒 ADD: hallucination verification
from Backend.legalchat.services.evidence_mapper import map_evidence, coverage_score

# 🧠 ADD: chat memory (NON-INTRUSIVE)
from Backend.legalchat.memory.session_memory import SessionMemory
from Backend.legalchat.services.semantic_context import SemanticContextBuilder

# ==================================================
# CHAT MEMORY LAYER (WRAPPER MODE)
# ==================================================

_session_memory = SessionMemory(max_turns=5)
_semantic_builder = SemanticContextBuilder()

# ==================================================
# HELPERS
# ==================================================

FOREIGN_KEYWORDS = [
    "america", "american", "us law", "usa",
    "united states", "uk law", "england",
    "california", "new york", "eu law", "gdpr",
    "at will employment"
]

def is_foreign_query(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in FOREIGN_KEYWORDS)

def looks_like_contract_clause(text: str) -> bool:
    """
    Strict detection: only trigger when text resembles
    an actual clause, not a legal question.
    """
    t = text.lower()

    clause_markers = [
        "neither party shall",
        "party shall indemnify",
        "shall be liable for",
        "confidential information",
        "governed by the laws of",
        "subject to arbitration",
        "limitation of liability"
    ]

    return any(m in t for m in clause_markers)

def base_response(query_id, timestamp, **kwargs):
    res = {
        "query_id": query_id,
        "timestamp": timestamp
    }
    res.update(kwargs)
    return res

def compute_confidence_details(citations: list, coverage_score_val: float):
    if not citations:
        statutory_support = 0.0
        relevance_component = 0.0
        coverage_component = coverage_score_val if isinstance(coverage_score_val, (int, float)) else 0.0
        doctrine_component = 0.0
    else:
        valid_citations = [c for c in citations if isinstance(c, dict) and c.get("validity_score", 0) > 0]
        if not valid_citations:
            statutory_support = 0.0
            relevance_component = 0.0
        else:
            statutory_support = min(len(valid_citations) / 4.0, 1.0)
            relevance_scores = [
                c.get("relevance_score", 0)
                for c in valid_citations
                if isinstance(c.get("relevance_score"), (int, float))
            ]
            relevance_component = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        coverage_component = coverage_score_val if isinstance(coverage_score_val, (int, float)) else 0.0
        has_declaratory = any(c.get("is_declaratory") for c in valid_citations) if valid_citations else False
        doctrine_component = 1.0 if has_declaratory else 0.0
    components = [statutory_support, relevance_component, coverage_component, doctrine_component]
    active = [c for c in components if c > 0]
    if active:
        raw = sum(active) / len(active)
    else:
        raw = 0.0
    confidence = round(min(max(float(raw), 0.0), 0.9), 2)
    factors = {
        "statutory_support": round(statutory_support, 2),
        "relevance": round(relevance_component, 2),
        "coverage": round(coverage_component, 2),
        "doctrine": round(doctrine_component, 2),
    }
    return confidence, factors

def annotate_citation_support(citations: list, evidence_map: list) -> list:
    if not isinstance(citations, list) or not isinstance(evidence_map, list):
        return citations
    grounded_sources = {
        e.get("evidence")
        for e in evidence_map
        if isinstance(e, dict) and e.get("grounded") and e.get("evidence")
    }
    annotated = []
    for c in citations:
        if not isinstance(c, dict):
            annotated.append(c)
            continue
        source = c.get("source")
        if not source:
            statute = c.get("statute") or ""
            identifier = c.get("identifier") or ""
            source = f"{statute} {identifier}".strip()
        supports = source in grounded_sources if source else False
        nc = dict(c)
        nc["supports_claim"] = bool(supports)
        annotated.append(nc)
    return annotated

# ==================================================
# ORIGINAL CORE ENGINE (UNCHANGED)
# ==================================================

def handle_query(user_query: str, semantic_enrichment: str = None) -> dict:
    query_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()

    # 🌍 Foreign law (single gate)
    if is_foreign_query(user_query):
        return base_response(
            query_id,
            timestamp,
            status="refused",
            domain="foreign_jurisdiction",
            reason="This system provides answers strictly based on Indian law"
        )

    # ==================================================
    # 🧾 CONTRACT CLAUSE PATH (NO REWRITE)
    # ==================================================
    if looks_like_contract_clause(user_query):
        # CONSTRAINT: Do NOT apply enrichment for contract clauses
        retrieval = retrieve_for_contract(user_query)
        analysis = generate_analysis(retrieval)

        analysis_lines = analysis.get("analysis", [])

        refined_lines = []
        if analysis_lines:
            refined_first = refine_analysis(analysis_lines[0])
            refined_lines.append(refined_first)
            refined_lines.extend(analysis_lines[1:])

        analysis_text = "\n".join(refined_lines) if refined_lines else "\n".join(analysis_lines)

        sentences = [
            s.strip()
            for s in analysis_text.replace("?", ".").replace("!", ".").split(".")
            if s.strip()
        ]

        retrieved_docs = (
            retrieval.get("documents")
            or retrieval.get("docs")
            or retrieval.get("citations")
            or []
        )

        if retrieved_docs and isinstance(retrieved_docs, list):
            patched_docs = []
            for d in retrieved_docs:
                if isinstance(d, dict) and "text" not in d:
                    patched_docs.append({
                        "text": f"{d.get('statute', '')} {d.get('identifier', '')}",
                        "source": f"{d.get('statute', '')} {d.get('identifier', '')}"
                    })
                else:
                    patched_docs.append(d)
            retrieved_docs = patched_docs

        evidence_map = map_evidence(sentences, retrieved_docs)
        coverage = coverage_score(evidence_map)
        citations = retrieval.get("citations", [])
        citations = annotate_citation_support(citations, evidence_map)
        confidence, confidence_factors = compute_confidence_details(citations, coverage)
        citation_support_map = {}
        for c in citations:
            if isinstance(c, dict):
                key = c.get("source") or f"{(c.get('statute') or '').strip()} {(c.get('identifier') or '').strip()}".strip()
                if key:
                    citation_support_map[key] = bool(c.get("supports_claim"))

        return base_response(
            query_id,
            timestamp,
            original_query=user_query,
            rewritten_query=user_query,

            status=analysis.get("status"),
            domain=retrieval.get("domain"),
            risk_level=analysis.get("risk_level") or retrieval.get("risk_level") or "medium",

            analysis_raw="\n".join(analysis_lines),
            analysis_user="\n".join(refined_lines),

            law_basis=analysis.get("law_basis"),
            confidence=confidence,
            citations=citations,

            coverage_score=coverage,
            evidence_map=evidence_map,
            citation_support_map=citation_support_map,
            confidence_factors=confidence_factors
        )

    # ==================================================
    # ❓ LEGAL QUESTION PATH (REWRITE ALLOWED)
    # ==================================================
    try:
        rewritten_query = rewrite_query(user_query)
    except Exception:
        return base_response(
            query_id,
            timestamp,
            status="refused",
            domain="rewrite_failure",
            reason="Query could not be normalized safely"
        )

    if not rewritten_query or not rewritten_query.strip():
        return base_response(
            query_id,
            timestamp,
            status="refused",
            domain="rewrite_failure",
            reason="Query normalization failed"
        )

    # 🧠 Apply semantic enrichment ONLY to retrieval query
    # CONSTRAINT: NEVER pass it to the LLM rewrite step (already done above)
    retrieval_query = rewritten_query
    if semantic_enrichment:
        # User Rule: Rewrite as "[previous legal subject] + [new constraint]"
        # semantic_enrichment contains the previous subject/domain keywords.
        retrieval_query = f"{semantic_enrichment} {rewritten_query}"

    retrieval = retrieve_for_contract(retrieval_query)
    analysis = generate_analysis(retrieval)

    analysis_lines = analysis.get("analysis", [])

    refined_lines = []
    if analysis_lines:
        refined_first = refine_analysis(analysis_lines[0])
        refined_lines.append(refined_first)
        refined_lines.extend(analysis_lines[1:])

    analysis_text = "\n".join(refined_lines) if refined_lines else "\n".join(analysis_lines)

    sentences = [
        s.strip()
        for s in analysis_text.replace("?", ".").replace("!", ".").split(".")
        if s.strip()
    ]

    retrieved_docs = (
        retrieval.get("documents")
        or retrieval.get("docs")
        or retrieval.get("citations")
        or []
    )

    if retrieved_docs and isinstance(retrieved_docs, list):
        patched_docs = []
        for d in retrieved_docs:
            if isinstance(d, dict) and "text" not in d:
                patched_docs.append({
                    "text": f"{d.get('statute', '')} {d.get('identifier', '')}",
                    "source": f"{d.get('statute', '')} {d.get('identifier', '')}"
                })
            else:
                patched_docs.append(d)
        retrieved_docs = patched_docs

    evidence_map = map_evidence(sentences, retrieved_docs)
    coverage = coverage_score(evidence_map)
    citations = retrieval.get("citations", [])
    citations = annotate_citation_support(citations, evidence_map)
    confidence, confidence_factors = compute_confidence_details(citations, coverage)
    citation_support_map = {}
    for c in citations:
        if isinstance(c, dict):
            key = c.get("source") or f"{(c.get('statute') or '').strip()} {(c.get('identifier') or '').strip()}".strip()
            if key:
                citation_support_map[key] = bool(c.get("supports_claim"))

    return base_response(
        query_id,
        timestamp,
        original_query=user_query,
        rewritten_query=rewritten_query,

        status=analysis.get("status"),
        domain=retrieval.get("domain"),
        risk_level=analysis.get("risk_level"),

        analysis_raw="\n".join(analysis_lines),
        analysis_user="\n".join(refined_lines),

        law_basis=analysis.get("law_basis"),
        confidence=confidence,
        citations=citations,

        coverage_score=coverage,
        evidence_map=evidence_map,
        citation_support_map=citation_support_map,
        confidence_factors=confidence_factors
    )

# ==================================================
# 🧠 CHAT-AWARE WRAPPER (NO CORE CHANGE)
# ==================================================

def handle_query_with_memory(user_query: str, session_id: str) -> dict:
    """
    Wrapper over handle_query().
    Core engine untouched.
    """

    if not session_id:
        session_id = "default"

    # 1. Fetch last <=5 semantic turns
    past_context = _session_memory.get_context(session_id)

    # 2. Build enrichment string
    semantic_enrichment = None
    locked_domain = None
    
    if past_context:
        # We pass empty string as first arg because we separate enrichment from query now
        enrichment_result = _semantic_builder.build("", past_context)
        semantic_enrichment = enrichment_result.get("enrichment_text")
        locked_domain = enrichment_result.get("locked_domain")

    # 3. Topic Switch Detection & Refinement Check
    current_domain = classify_domain(user_query)
    
    # If explicit switch (and not general refinement)
    if locked_domain and current_domain != "general" and current_domain != locked_domain:
        # User switched topic (e.g. from contract to criminal)
        # Clear enrichment to allow fresh retrieval
        semantic_enrichment = None
        print(f"[SEMANTIC_MEMORY] Topic Switch Detected: {locked_domain} -> {current_domain}. Context cleared.")
    
    # 4. Call core engine (Enrichment applied ONLY to retrieval, NOT rewrite)
    response = handle_query(user_query, semantic_enrichment=semantic_enrichment)

    if response.get("status") == "no_authoritative_source" and locked_domain and semantic_enrichment:
        print("[SEMANTIC_MEMORY] UNKNOWN detected despite lock. Attempting fallback to locked doctrine.")
        synthetic_query = f"{user_query} {semantic_enrichment}"
        base_case = resolve_base_case(synthetic_query, locked_domain)
        
        if base_case:
             analysis_text = base_case["analysis"]
             sentences = [analysis_text] if isinstance(analysis_text, str) else []
             evidence_map = map_evidence(sentences, [])
             coverage = coverage_score(evidence_map)
             citations = []
             confidence, confidence_factors = compute_confidence_details(citations, coverage)
             response = base_response(
                response["query_id"],
                response["timestamp"],
                original_query=user_query,
                rewritten_query=user_query,
                status=base_case["status"],
                domain=locked_domain,
                risk_level=base_case["risk_level"],
                analysis_raw=analysis_text,
                analysis_user=analysis_text,
                law_basis=base_case["law_basis"],
                confidence=confidence,
                citations=citations,
                coverage_score=coverage,
                evidence_map=evidence_map,
                citation_support_map={},
                confidence_factors=confidence_factors
             )
             print(f"[SEMANTIC_MEMORY] Recovered using locked doctrine: {base_case['law_basis']}")

    # LOGGING (Back-end only)
    # Check if enrichment was actually potentially used (i.e. not a clause)
    if semantic_enrichment and not looks_like_contract_clause(user_query):
        print(f"[SEMANTIC_MEMORY] Applied enrichment: {semantic_enrichment}")

    try:
        # 5. Extract metadata (Strictly NO raw text)
        citations = response.get("citations", [])
        statutes = []
        sections = []
        
        if isinstance(citations, list):
            for c in citations:
                if isinstance(c, dict):
                    if c.get("statute"):
                        statutes.append(c.get("statute"))
                    if c.get("identifier"):
                        sections.append(c.get("identifier"))
        
        # Deduplicate
        statutes = list(set(statutes))
        sections = list(set(sections))
        
        # Extract Doctrine
        primary_doctrine = response.get("law_basis")

        _session_memory.add_turn(
            session_id=session_id,
            semantic_data={
                "verdict_type": response.get("status"),
                "legal_domain": response.get("domain"),
                "statute_names": statutes,
                "section_numbers": sections,
                "primary_doctrine": primary_doctrine
            }
        )
    except Exception:
        pass

    return response

# ==================================================
# LOCAL TEST RUN
# ==================================================

if __name__ == "__main__":
    tests = [
        "Is a confidentiality clause legally enforceable in India?",
        # "Can an employee be terminated without notice in India?",
        # "Is an arbitration clause valid under Indian law?",
        # "Will I be fired for abusing my boss",
        # "Is non-compete enforceable under UK law?",
        # "Can an employer enforce a post-employment non-compete clause in India?",
        # "Is emotional harassment at workplace illegal in India?"
    ]

    for q in tests:
        print("\n" + "=" * 100)
        print("USER QUERY:", q)
        response = handle_query_with_memory(q, session_id="demo123")
        print("RESPONSE:")
        for k, v in response.items():
            print(f"{k}: {v}")

# Custom Clause Reject

#1. The Employee shall not, for a period of five years after termination of
# employment, engage in any business or employment that is similar to or
# competitive with the Company anywhere in India.

#2. The Employee shall not, for a period of five (5) years after termination of
# employment, engage in any business, profession, or employment that is similar
# to or competes with the business of the Company anywhere in India or abroad.

# 3. The Employee agrees that upon breach of this agreement, the Company may initiate
# criminal proceedings and ensure imprisonment of the Employee


# Custom Clause Accept

# Each party shall keep all Confidential Information strictly confidential
# and shall not disclose such information to any third party without the
# prior written consent of the disclosing party, except as required by law.
# This obligation shall survive termination of this Agreement.
