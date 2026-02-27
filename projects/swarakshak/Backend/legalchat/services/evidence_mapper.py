# legalchat/services/evidence_mapper.py
# Minimal, robust sentence <-> evidence mapper.
# Tries to use SentenceTransformers if available for embeddings & cosine similarity.
# Falls back to a cheap token-overlap similarity if not available.

import math

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_ST = True
except Exception:
    _HAS_ST = False

import numpy as np
import re

DEFAULT_THRESHOLD = 0.75  # tuneable: 0.7-0.8 is reasonable for legal grounding

def _simple_token_similarity(a: str, b: str) -> float:
    # cheap fallback: Jaccard over words
    wa = set(re.findall(r"\w+", a.lower()))
    wb = set(re.findall(r"\w+", b.lower()))
    if not wa or not wb:
        return 0.0
    inter = wa & wb
    union = wa | wb
    return len(inter) / len(union)

def _to_numpy(x):
    if hasattr(x, "cpu"):  # torch tensor
        return x.cpu().numpy()
    return np.array(x)

def map_evidence(answer_sentences, retrieved_docs, embedder=None, threshold=DEFAULT_THRESHOLD):
    """
    answer_sentences: list[str]
    retrieved_docs: list[dict] each dict should ideally have:
        - 'text' or 'content' : string
        - 'source' : identifier (filename, id, citation)
        - optionally 'embedding' : vector (numpy or torch)
    embedder: optional SentenceTransformer instance (or any object with .encode)
    threshold: similarity threshold to mark grounded
    Returns: list of mappings for each sentence:
      { sentence, evidence, score, grounded, evidence_snippet (optional) }
    """
    docs = []
    for d in retrieved_docs or []:
        text = d.get("text") or d.get("content") or d.get("chunk") or d.get("body") or d.get("doc_text") or ""
        source = d.get("source") or d.get("id") or d.get("doc_id") or d.get("filename") or d.get("meta") or "unknown"
        emb = d.get("embedding") or d.get("emb") or None
        docs.append({"text": text, "source": source, "embedding": emb})

    # Prepare embedder if possible
    st = embedder
    if st is None and _HAS_ST:
        try:
            st = SentenceTransformer("all-mpnet-base-v2")  # small but strong; replace if you have a local model
        except Exception:
            st = None

    # If docs don't have embeddings but we have st, compute doc embeddings
    if st is not None:
        # compute doc embeddings where missing
        texts_to_encode = []
        idx_map = []
        for i, doc in enumerate(docs):
            if doc["embedding"] is None:
                texts_to_encode.append(doc["text"][:10000])  # truncate long docs
                idx_map.append(i)
        if texts_to_encode:
            try:
                encoded = st.encode(texts_to_encode, convert_to_tensor=True, show_progress_bar=False)
                for j, idx in enumerate(idx_map):
                    docs[idx]["embedding"] = encoded[j]
            except Exception:
                # Fall back: leave embedding None for those docs
                pass

    # Now for each sentence, compute best doc and score
    evidence_map = []
    for sent in answer_sentences:
        best_score = 0.0
        best_doc = None

        # sentence embedding if possible
        sent_emb = None
        if st is not None:
            try:
                sent_emb = st.encode(sent, convert_to_tensor=True)
            except Exception:
                sent_emb = None

        for doc in docs:
            score = 0.0
            if doc.get("embedding") is not None and sent_emb is not None:
                try:
                    # use sentence_transformers util if available
                    if _HAS_ST and hasattr(util, "cos_sim"):
                        score = util.cos_sim(sent_emb, doc["embedding"]).item()
                    else:
                        # numeric fallback: dot / norms
                        se = _to_numpy(sent_emb)
                        de = _to_numpy(doc["embedding"])
                        if se.ndim == 1 and de.ndim == 1:
                            denom = (np.linalg.norm(se) * np.linalg.norm(de))
                            score = float(np.dot(se, de) / denom) if denom else 0.0
                except Exception:
                    score = 0.0
            else:
                # fallback to token overlap similarity
                score = _simple_token_similarity(sent, doc["text"])

            if score > best_score:
                best_score = score
                best_doc = doc

        grounded = best_score >= threshold
        evidence_map.append({
            "sentence": sent,
            "evidence": best_doc["source"] if best_doc else None,
            "evidence_snippet": (best_doc["text"][:500] if best_doc else None),
            "score": round(float(best_score), 3),
            "grounded": bool(grounded)
        })

    return evidence_map

def coverage_score(evidence_map):
    grounded = sum(1 for e in evidence_map if e.get("grounded"))
    total = len(evidence_map)
    return round(grounded / total, 2) if total else 0
