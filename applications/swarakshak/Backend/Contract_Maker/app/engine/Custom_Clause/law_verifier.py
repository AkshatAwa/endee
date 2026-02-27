from Backend.legalchat.services.retrieval import retrieve_for_contract

def verify_clause_legality(clause_text: str) -> dict:
    """
    Uses Indian-law-only retrieval engine.
    """

    query = f"Enforceability of the following NDA clause under Indian contract law: {clause_text}"

    result = retrieve_for_contract(query)

    if not result:
        return {
            "status": "unknown",
            "reason": "No legal material found"
        }

    return result
