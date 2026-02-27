# =====================================================
# DOWNLOAD GENERATED PDF
# =====================================================
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from Backend.LegalAPI.app.auth.api_key import validate_api_key

from Backend.Contract_Maker.app.engine.Default_Clause.generate_nda import generate_nda_json
from Backend.Contract_Maker.app.engine.Default_Clause.nda_pdf import generate_nda_pdf
from Backend.Contract_Maker.app.engine.Custom_Clause.clause_pipeline import process_user_prompt

import os, uuid

router = APIRouter(prefix="/draft", tags=["Contract Drafting"])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

OUTPUT_DIR = os.path.join(
    BASE_DIR, "Contract_Maker", "app", "engine", "output"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------
# AUTH
# ---------------------------
def auth_check(auth: str):
    if not auth:
        raise HTTPException(status_code=401, detail="API key missing")
    api_key = auth.replace("Bearer ", "")
    if not validate_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")


# =====================================================
# DEFAULT NDA – PREVIEW (JSON ONLY)  ❌ UNCHANGED
# =====================================================
@router.post("/default/preview")
def preview_default_nda(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)
    nda = generate_nda_json(payload)
    return {"status": "preview", "nda": nda}


# =====================================================
# DEFAULT NDA – GENERATE PDF ❌ UNCHANGED
# =====================================================
@router.post("/default/generate")
def generate_default_nda(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)

    nda = generate_nda_json(payload)

    file_id = uuid.uuid4().hex[:8]
    pdf_path = os.path.join(OUTPUT_DIR, f"nda_{file_id}.pdf")

    generate_nda_pdf(nda, pdf_path)

    return {
        "status": "generated",
        "download_url": f"/v1/draft/download/{file_id}"
    }


# =====================================================
# 🔥 DEFAULT NDA – PREVIEW + PDF (NEW)
# =====================================================
@router.post("/default/preview-pdf")
def preview_default_nda_pdf(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)

    nda = generate_nda_json(payload)

    file_id = uuid.uuid4().hex[:8]
    pdf_path = os.path.join(OUTPUT_DIR, f"nda_preview_{file_id}.pdf")

    generate_nda_pdf(nda, pdf_path)

    return {
        "status": "preview",
        "nda": nda,
        "download_url": f"/v1/draft/download/{file_id}"
    }


# =====================================================
# CUSTOM CLAUSE – PREVIEW (JSON ONLY) ❌ UNCHANGED
# =====================================================
@router.post("/custom/preview")
def preview_custom_clause(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)

    base_data = payload.get("base_data")
    clause_prompt = payload.get("clause_prompt")

    if not base_data or not clause_prompt:
        raise HTTPException(status_code=400, detail="Invalid payload")

    nda = generate_nda_json(base_data)
    result = process_user_prompt(clause_prompt, nda)

    return {
        "status": "preview",
        "analysis": result,
        "nda": nda
    }


# =====================================================
# CUSTOM CLAUSE – GENERATE PDF ❌ UNCHANGED
# =====================================================
@router.post("/custom/generate")
def generate_custom_clause(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)

    base_data = payload.get("base_data")
    clause_prompt = payload.get("clause_prompt")

    nda = generate_nda_json(base_data)
    result = process_user_prompt(clause_prompt, nda)

    if result["status"] != "added":
        return result

    file_id = uuid.uuid4().hex[:8]
    pdf_path = os.path.join(OUTPUT_DIR, f"nda_custom_{file_id}.pdf")

    generate_nda_pdf(nda, pdf_path)

    return {
        "status": "generated",
        "download_url": f"/v1/draft/download/{file_id}"
    }


# =====================================================
# 🔥 CUSTOM CLAUSE – PREVIEW + PDF (NEW)
# =====================================================
@router.post("/custom/preview-pdf")
def preview_custom_clause_pdf(payload: dict, authorization: str = Header(None)):
    auth_check(authorization)

    base_data = payload.get("base_data")
    clause_prompt = payload.get("clause_prompt")

    if not base_data or not clause_prompt:
        raise HTTPException(status_code=400, detail="Invalid payload")

    nda = generate_nda_json(base_data)
    result = process_user_prompt(clause_prompt, nda)

    if result["status"] != "added":
        return result

    file_id = uuid.uuid4().hex[:8]
    pdf_path = os.path.join(OUTPUT_DIR, f"nda_preview_{file_id}.pdf")

    generate_nda_pdf(nda, pdf_path)

    return {
        "status": "preview",
        "analysis": result,
        "nda": nda,
        "download_url": f"/v1/draft/download/{file_id}"
    }


# =====================================================
# DOWNLOAD (DEFAULT + CUSTOM) ❌ UNCHANGED
# =====================================================
@router.get("/download/{file_id}")
def download_nda(file_id: str):
    pdf_path = os.path.join(OUTPUT_DIR, f"nda_{file_id}.pdf")

    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(OUTPUT_DIR, f"nda_custom_{file_id}.pdf")

    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(OUTPUT_DIR, f"nda_preview_{file_id}.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="nda.pdf"
    )
