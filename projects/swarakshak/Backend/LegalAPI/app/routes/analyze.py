from fastapi import APIRouter, Header, HTTPException
from Backend.LegalAPI.app.auth.api_key import validate_api_key

# 🔥 IMPORT LEGALCHAT BRAIN
from Backend.legalchat.api.ask import handle_query

import time
import uuid

router = APIRouter()


@router.post("/analyze")
def analyze(payload: dict, authorization: str = Header(None)):
    # 🔐 API KEY CHECK
    if not authorization:
        raise HTTPException(status_code=401, detail="API key missing")

    api_key = authorization.replace("Bearer ", "")
    if not validate_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    user_query = payload.get("query")
    jurisdiction = payload.get("jurisdiction", "IN")

    if not user_query:
        raise HTTPException(status_code=400, detail="Query missing")

    # 🧠 CALL LEGALCHAT ASK ENGINE (FULL PIPELINE)
    result = handle_query(user_query)

    # 🔁 Wrap with API metadata (no logic change)
    return {
        "id": f"req_{uuid.uuid4().hex[:10]}",
        "object": "legal.analysis",
        "created": int(time.time()),
        "jurisdiction": jurisdiction,

        # 🔑 DIRECT LEGALCHAT OUTPUT
        "status": result.get("status"),
        "risk_level": result.get("risk_level"),

        "answer": result.get("analysis_user"),
        "analysis": result.get("analysis_raw"),

        "law_basis": result.get("law_basis"),
        "confidence": result.get("confidence"),
        "citations": result.get("citations", [])
    }
