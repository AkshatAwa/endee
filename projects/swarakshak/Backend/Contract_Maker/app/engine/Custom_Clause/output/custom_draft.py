from fastapi import APIRouter, Header, HTTPException
from typing import Dict
import json
import os

from Backend.LegalAPI.app.auth.api_key import validate_api_key
from Backend.Contract_Maker.app.engine.Default_Clause.generate_nda import generate_nda_json
from Backend.Contract_Maker.app.engine.Custom_Clause.clause_pipeline import process_user_prompt

router = APIRouter(prefix="/v1/draft", tags=["Custom Draft"])


@router.post("/custom")
def generate_custom_nda(
    payload: Dict,
    authorization: str = Header(None)
):
    # 🔐 API KEY CHECK
    if not authorization:
        raise HTTPException(status_code=401, detail="API key missing")

    api_key = authorization.replace("Bearer ", "")
    if not validate_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    # 🧾 Required fields
    required = [
        "party1_name",
        "party1_short_name",
        "party1_address",
        "party2_name",
        "party2_address",
        "proposed_transaction",
        "execution_date",
        "custom_prompt"
    ]

    for field in required:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    # 1️⃣ Generate base NDA
    nda = generate_nda_json(payload)

    # 2️⃣ Process custom clause
    clause_result = process_user_prompt(
        payload["custom_prompt"],
        nda
    )

    if clause_result["status"] != "added":
        return {
            "status": "rejected",
            "reason": clause_result.get("reason", "Clause rejected"),
            "analysis": clause_result
        }

    # 3️⃣ Preview response
    return {
        "status": "preview",
        "nda": nda,
        "custom_clause": clause_result.get("analysis")
    }
