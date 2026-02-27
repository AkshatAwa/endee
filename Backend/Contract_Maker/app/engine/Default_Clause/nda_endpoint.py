from fastapi import APIRouter
from pathlib import Path
from Backend.Contract_Maker.app.engine.Default_Clause.generate_nda import generate_nda_json
from Backend.Contract_Maker.app.engine.Default_Clause.nda_pdf import generate_nda_pdf

router = APIRouter()

PDF_OUTPUT_DIR = Path("generated_pdfs")
PDF_OUTPUT_DIR.mkdir(exist_ok=True)


@router.post("/generate-nda")
def generate_nda(payload: dict):
    nda_json = generate_nda_json(payload)

    pdf_path = PDF_OUTPUT_DIR / "nda_generated.pdf"
    generate_nda_pdf(nda_json, str(pdf_path))

    return {
        "status": "success",
        "nda": nda_json,
        "pdf_path": str(pdf_path)
    }
