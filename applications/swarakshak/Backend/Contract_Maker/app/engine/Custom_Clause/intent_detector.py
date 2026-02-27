def detect_intent(user_input: str) -> dict:
    t = user_input.lower()

    if any(k in t for k in [
        "confidential", "nda", "non disclosure",
        "secret", "data", "information", "source code"
    ]):
        return {"intent": "nda_confidentiality"}

    if any(k in t for k in [
        "penalty", "fine", "recover", "damages"
    ]):
        return {"intent": "nda_breach_consequence"}

    if any(k in t for k in [
        "terminate", "termination", "after leaving", "post employment"
    ]):
        return {"intent": "nda_survival"}

    return {"intent": "unknown"}
