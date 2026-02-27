from .intent_detector import detect_intent
from .ollama_nda_writer import generate_nda_clause
from .law_verifier import verify_clause_legality
from .clause_validator import validate_nda_clause


# ==================================================
# 🚫 SEMANTIC HARD GUARD
# Mandatory legal disclosure cannot be overridden
# ==================================================
def violates_mandatory_disclosure(clause_text: str) -> bool:
    t = clause_text.lower()

    # 🚨 Phrases that indicate override of law/court
    override_indicators = [
        "notwithstanding",
        "shall not be relieved",
        "regardless of",
        "even if required",
        "even when required",
        "irrespective of",
        "continue to be bound",
        "despite any requirement",
        "despite any order"
    ]

    # 🚨 Authority references
    authority_indicators = [
        "law",
        "court",
        "court order",
        "judicial",
        "regulatory",
        "administrative agency",
        "government authority",
        "statutory"
    ]

    # ✅ Legal carve-outs (these SAVE the clause)
    valid_exceptions = [
        "except as required by law",
        "subject to applicable law",
        "to the extent required by law",
        "provided that disclosure is required by law",
        "as required by law"
    ]

    # If clause tries to override authority WITHOUT exception → illegal
    if (
        any(o in t for o in override_indicators)
        and any(a in t for a in authority_indicators)
        and not any(v in t for v in valid_exceptions)
    ):
        return True

    return False


def detect_clause_intent(clause_text: str) -> str:
    t = clause_text.lower()
    confidentiality_keywords = [
        "confidential",
        "nda",
        "non disclosure",
        "non-disclosure",
        "trade secret",
        "proprietary",
        "confidential information"
    ]
    non_compete_keywords = [
        "non compete",
        "non-compete",
        "shall not compete",
        "not compete",
        "competing business",
        "engage in any business",
        "similar business",
        "compete with"
    ]
    if any(k in t for k in confidentiality_keywords):
        return "confidentiality"
    if any(k in t for k in non_compete_keywords):
        return "non_compete"
    return "other"


# ==================================================
# MAIN PIPELINE
# ==================================================
def process_user_prompt(user_input: str, nda_json: dict) -> dict:

    # 1️⃣ Intent
    intent_data = detect_intent(user_input)
    intent = intent_data["intent"]

    if intent == "unknown":
        return {
            "status": "rejected",
            "reason": "Intent not understood"
        }

    # 2️⃣ Draft NDA language
    clause_text = generate_nda_clause(intent, user_input)
    if not clause_text:
        return {
            "status": "rejected",
            "reason": "Clause drafting failed"
        }
    clause_intent = detect_clause_intent(clause_text)

    # ==================================================
    # 🚫 SEMANTIC LEGAL GUARD (CRITICAL)
    # ==================================================
    if violates_mandatory_disclosure(clause_text):
        return {
            "status": "rejected",
            "reason": (
                "A confidentiality clause cannot override or negate a legal or "
                "court-mandated disclosure. Such clauses are void under Indian law "
                "as they violate public policy."
            )
        }

    # 3️⃣ Verify with Indian law engine
    law_result = verify_clause_legality(clause_text)

    # 4️⃣ Validate
    validation = validate_nda_clause(clause_text, law_result, clause_intent=clause_intent)

    if validation["status"] != "approved":
        return validation

    # 5️⃣ Add to NDA
    clause = {
        "clause_number": "NEW",
        "title": "Custom NDA Clause",
        "text": clause_text
    }

    nda_json["clauses"].append(clause)

    return {
        "status": "added",
        "clause": clause,
        "analysis": validation
    }
