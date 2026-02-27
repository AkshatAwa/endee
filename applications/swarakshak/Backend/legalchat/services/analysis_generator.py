from typing import Dict, List, Optional

NON_ADVICE_PREFIX = (
    "Based on applicable Indian law and judicial interpretation, "
    "the following position emerges for informational purposes only: "
)

# --------------------------------------------------
# FINAL VERDICT LINE (NEW – PURE ADDITION)
# --------------------------------------------------

def _verdict_to_line(verdict: str) -> str:
    if verdict == "LEGAL":
        return "Final Verdict: YES (This is legally allowed under Indian law.)"
    if verdict == "ILLEGAL":
        return "Final Verdict: NO (This is not legally allowed in most cases.)"
    if verdict == "DEPENDS":
        return "Final Verdict: DEPENDS (This depends on conditions and facts.)"
    if verdict == "UNKNOWN":
        return "Final Verdict: NOT CLEAR (Law does not give a clear answer.)"
    return "Final Verdict: DEPENDS (Outcome depends on legal details.)"

def _final_verdict_line(status: str, risk_level: str, verdict: Optional[str] = None) -> str:
    if verdict:
        return _verdict_to_line(verdict)
    if status in {"illegal", "high_risk"}:
        return "Final Verdict: NO (This is not legally allowed in most cases.)"
    if status == "legal":
        return "Final Verdict: YES (This is legally allowed under Indian law.)"
    if status == "legal_with_conditions" or risk_level == "medium":
        return "Final Verdict: DEPENDS (This depends on conditions and facts.)"
    if status == "no_authoritative_source":
        return "Final Verdict: NOT CLEAR (Law does not give a clear answer.)"
    return "Final Verdict: DEPENDS (Outcome depends on legal details.)"


# --------------------------------------------------
# MAIN ANALYSIS GENERATOR (UNCHANGED LOGIC)
# --------------------------------------------------

def generate_analysis(retrieval_result: Dict) -> Dict:
    """
    Converts retrieval output into a structured legal analysis.
    Deterministic, rule-driven, and non-advisory.
    """

    # --------------------------------------------------
    # REFUSAL / NO SOURCE
    # --------------------------------------------------
    if retrieval_result.get("status") in ["refused", "no_authoritative_source"]:
        analysis_text = retrieval_result.get(
            "reason",
            "No authoritative Indian legal source could be identified for the given query."
        )

        verdict = _final_verdict_line(
            retrieval_result.get("status"),
            "unknown",
            retrieval_result.get("verdict")
        )

        return {
            "status": retrieval_result.get("status"),
            "risk_level": "unknown",
            "analysis": [
                analysis_text,
                verdict
            ],
            "law_basis": None,
            "confidence": retrieval_result.get("confidence", 0.0)
        }

    # --------------------------------------------------
    # PASS-THROUGH FROM RETRIEVAL (BASE CASE)
    # --------------------------------------------------
    if "analysis" in retrieval_result and "law_basis" in retrieval_result:
        analysis_points: List[str] = retrieval_result.get("analysis", [])

        if analysis_points:
            analysis_text = NON_ADVICE_PREFIX + analysis_points[0]
        else:
            analysis_text = NON_ADVICE_PREFIX + "Relevant statutory provisions apply."

        verdict = _final_verdict_line(
            retrieval_result.get("status"),
            retrieval_result.get("risk_level"),
            retrieval_result.get("verdict")
        )

        return {
            "status": retrieval_result.get("status", "ok"),
            "risk_level": retrieval_result.get("risk_level"),
            "analysis": [
                analysis_text,
                verdict
            ],
            "law_basis": retrieval_result.get("law_basis"),
            "confidence": retrieval_result.get("confidence", 0.0)
        }

    domain = retrieval_result.get("domain")
    generic_map = {
        "employment_contract": (
            "Employment relationships in India are regulated by statutory labour protections, "
            "and any termination or disciplinary action must comply with applicable law."
        ),
        "labour_law": (
            "Labour-related matters in India are governed by welfare legislation intended "
            "to protect workmen against arbitrary action."
        ),
        "contract_clause": (
            "Contractual clauses are enforceable in India subject to statutory limitations, "
            "public policy considerations, and judicial scrutiny."
        )
    }
    generic_analysis = generic_map.get(
        domain,
        "The legal position depends on applicable Indian statutes and judicial precedents."
    )
    verdict = _final_verdict_line(
        retrieval_result.get("status", "ok"),
        retrieval_result.get("risk_level"),
        retrieval_result.get("verdict")
    )
    return {
        "status": retrieval_result.get("status", "ok"),
        "risk_level": retrieval_result.get("risk_level"),
        "analysis": [
            NON_ADVICE_PREFIX + generic_analysis,
            verdict
        ],
        "law_basis": retrieval_result.get("law_basis"),
        "confidence": retrieval_result.get("confidence", 0.0)
    }
