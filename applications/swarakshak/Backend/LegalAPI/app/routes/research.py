from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi import Header
from Backend.LegalAPI.app.auth.api_key import validate_api_key
from Backend.legalchat.services.retrieval import (
    classify_domain,
    get_candidate_indices,
    faiss_rank_with_scores,
    METADATA,
    DOCUMENTS,
)
from Backend.legalchat.services.retrieval import (
    _extract_section_no,
    _keyword_overlap_score,
)
from Backend.legalchat.services.retrieval import infer_risk_level
import re
from typing import List, Dict, Any
import io

router = APIRouter(prefix="/research", tags=["Deep Research"])

def _read_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def _read_pdf(content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        raise HTTPException(status_code=500, detail="PDF processing not available")
    try:
        reader = PdfReader(io.BytesIO(content))
        out = []
        for page in reader.pages:
            text = page.extract_text() or ""
            out.append(text)
        return "\n".join(out)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read PDF")

def _read_docx(content: bytes) -> str:
    try:
        import docx
    except Exception:
        raise HTTPException(status_code=500, detail="DOCX processing not available")
    try:
        f = io.BytesIO(content)
        document = docx.Document(f)
        paras = [p.text for p in document.paragraphs]
        return "\n".join(paras)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read DOCX")

def _extract_text(file: UploadFile) -> str:
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    ct = (file.content_type or "").lower()
    name = (file.filename or "").lower()
    if "pdf" in ct or name.endswith(".pdf"):
        return _read_pdf(content)
    if "docx" in ct or name.endswith(".docx"):
        return _read_docx(content)
    return _read_txt(content)

def _chunk_text(text: str, max_len: int = 1200) -> List[str]:
    lines = [l.strip() for l in text.splitlines()]
    paras: List[str] = []
    buf = []
    length = 0
    for l in lines:
        if not l:
            if buf:
                paras.append("\n".join(buf))
                buf = []
                length = 0
            continue
        if length + len(l) > max_len:
            if buf:
                paras.append("\n".join(buf))
            buf = [l]
            length = len(l)
        else:
            buf.append(l)
            length += len(l)
    if buf:
        paras.append("\n".join(buf))
    return [p for p in paras if p.strip()]

def _legal_concepts(text: str) -> List[str]:
    t = text.lower()
    concepts = []
    if any(k in t for k in ["confidential", "confidentiality"]):
        concepts.append("confidentiality")
    if any(k in t for k in ["indemnity", "indemnify"]):
        concepts.append("indemnity")
    if "arbitration" in t:
        concepts.append("arbitration")
    if any(k in t for k in ["non compete", "non-compete", "restraint of trade"]):
        concepts.append("non_compete")
    if any(k in t for k in ["termination", "dismiss", "discharge", "retrench"]):
        concepts.append("termination")
    return concepts or ["general"]

def _semantic_from_distance(d: float) -> float:
    return 1.0 / (1.0 + max(0.0, d))

def _retrieve_for_chunk(chunk: str) -> List[Dict[str, Any]]:
    domain = classify_domain(chunk)
    indices = get_candidate_indices(domain)
    if not indices:
        return []
    ranked = faiss_rank_with_scores(chunk, indices, k=8)
    results = []
    for idx, dist in ranked:
        m = METADATA[idx]
        statute = m.get("statute")
        identifier = m.get("identifier", "")
        section = _extract_section_no(identifier) or ""
        doc_text = DOCUMENTS[idx] if idx < len(DOCUMENTS) else ""
        semantic = _semantic_from_distance(dist)
        overlap = _keyword_overlap_score(chunk, doc_text)
        confidence = round((semantic + overlap) / 2.0, 4)
        if statute:
            results.append({
                "statute": statute,
                "section": section,
                "matched_text": doc_text,
                "confidence": confidence
            })
    return results[:5]

def _summarize_document(text: str) -> str:
    words = re.findall(r"\w+", text.lower())
    freq = {}
    for w in words:
        if len(w) < 4:
            continue
        freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]
    terms = ", ".join(t for t, _ in top)
    return f"Document mentions: {terms}" if terms else "No salient terms detected"

@router.post("/analyze")
async def deep_analyze(
    file: UploadFile = File(...),
    deep_mode: bool = Form(True),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="API key missing")
    api_key = authorization.replace("Bearer ", "")
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not deep_mode:
        raise HTTPException(status_code=400, detail="Deep mode must be enabled")

    try:
        text = _extract_text(file)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process file")

    chunks = _chunk_text(text)
    if not chunks:
        return {
            "error": "No readable text found in document",
            "final_verdict": "No",
            "confidence": 0.0
        }

    issues: List[Dict[str, Any]] = []
    all_citations: List[Dict[str, Any]] = []
    for ch in chunks:
        concepts = _legal_concepts(ch)
        citations = _retrieve_for_chunk(ch)
        all_citations.extend(citations)
        domain = classify_domain(ch)
        risk = infer_risk_level(domain, [{"statute": c["statute"]} for c in citations])
        analysis_text = "Retrieved statutory sections relevant to the provided content. Explanation is strictly limited to retrieved text."
        ambiguities = "Insufficient statutory basis" if not citations else ""
        issues.append({
            "issue": concepts[0],
            "analysis": analysis_text,
            "citations": citations,
            "ambiguities": ambiguities,
            "risk_level": (risk or "unknown").upper() if isinstance(risk, str) else "UNKNOWN"
        })

    if not all_citations:
        final_verdict = "No"
        overall_conf = 0.0
    else:
        final_verdict = "Conditional with reason"
        scores = [c["confidence"] for c in all_citations]
        overall_conf = round(sum(scores) / max(1, len(scores)), 4)

    return {
        "document_summary": _summarize_document(text),
        "issues_identified": issues,
        "final_verdict": final_verdict,
        "confidence": overall_conf
    }

