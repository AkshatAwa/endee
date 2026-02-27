from typing import Optional


def validate_nda_clause(clause_text: str, law_result: dict, clause_intent: Optional[str] = None) -> dict:
    status = law_result.get("status")
    basis_parts = []
    for key in ["law_basis", "reason"]:
        val = law_result.get(key)
        if val:
            basis_parts.append(str(val))
    analysis = law_result.get("analysis")
    if isinstance(analysis, list):
        basis_parts.extend([str(a) for a in analysis if a])
    elif analysis:
        basis_parts.append(str(analysis))
    basis_text = " ".join(basis_parts).lower()
    section_27_flag = "section 27" in basis_text or "restraint of trade" in basis_text

    if status == "refused":
        return {
            "status": "rejected",
            "reason": "Clause violates Indian public policy or law"
        }

    if status == "no_authoritative_source":
        return {
            "status": "rejected",
            "reason": "Clause not supported by Indian law"
        }

    if status == "legal":
        return {
            "status": "approved",
            "confidence": law_result.get("confidence", 0.6),
            "citations": law_result.get("citations", [])
        }

    if status == "legal_with_conditions" and clause_intent == "confidentiality":
        return {
            "status": "approved",
            "confidence": law_result.get("confidence", 0.6),
            "citations": law_result.get("citations", [])
        }

    if status == "illegal" and clause_intent == "confidentiality" and section_27_flag:
        return {
            "status": "approved",
            "confidence": law_result.get("confidence", 0.6),
            "citations": law_result.get("citations", [])
        }

    return {
        "status": "rejected",
        "reason": "Unclear legal position"
    }
