import json
import copy
import re
import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

NDA_TEMPLATE_PATH = (
    BASE_DIR
    / "templates"
    / "Doc_json"
    / "Non_Disclosure_Agreement.json"
)

def generate_nda_json(user_input: dict) -> dict:
    # 1️⃣ Load template
    with open(NDA_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        nda_template = json.load(f)

    nda = copy.deepcopy(nda_template)

    # 2️⃣ 🔥 SET VARIABLES (THIS WAS MISSING)
    nda["variables"] = {
        "party1_name": user_input.get("party1_name"),
        "party1_short_name": user_input.get("party1_short_name"),
        "party1_address": user_input.get("party1_address"),
        "party2_name": user_input.get("party2_name"),
        "party2_address": user_input.get("party2_address"),
        "proposed_transaction": user_input.get("proposed_transaction"),
        "execution_date": user_input.get("execution_date"),
    }

    # 3️⃣ Text replacements
    replacements = {
        r"<Party 1>": nda["variables"]["party1_name"],
        r"<<address>>": nda["variables"]["party1_address"],
        r"\[Please fill in Customers name\]": nda["variables"]["party2_name"],
        r"\[Please fill in address\]": nda["variables"]["party2_address"],
        r"\[Please fill in details of proposed transaction\]": nda["variables"]["proposed_transaction"],
        r"_________ day of _________, 2016": nda["variables"]["execution_date"],
        r"____": nda["variables"]["party1_short_name"],
    }

    # 4️⃣ Apply replacement ONLY on Preamble
    for clause in nda.get("clauses", []):
        if clause.get("clause_number") == "P":
            text = clause.get("text", "")
            for pattern, value in replacements.items():
                if value:
                    text = re.sub(pattern, value, text)
            clause["text"] = text
            break

    return nda


# =====================================================
# 🔥 NEW FUNCTION – PREVIEW PDF GENERATOR
# (Existing code above is UNTOUCHED)
# =====================================================

def generate_nda_preview_pdf(
    user_input: dict,
    output_dir: str
) -> dict:
    """
    Preview-only helper function

    - Does NOT modify existing logic
    - Uses generate_nda_json()
    - Uses existing PDF engine (generate_nda_pdf)
    - Creates a temporary preview PDF
    """

    # Import here to avoid touching existing imports
    from Backend.Contract_Maker.app.engine.Default_Clause.nda_pdf import generate_nda_pdf

    # 1️⃣ Reuse existing JSON generator
    nda_json = generate_nda_json(user_input)

    # 2️⃣ Create preview file
    file_id = uuid.uuid4().hex[:8]
    preview_path = os.path.join(
        output_dir,
        f"nda_preview_{file_id}.pdf"
    )

    # 3️⃣ Reuse existing PDF generator
    generate_nda_pdf(nda_json, preview_path)

    return {
        "file_id": file_id,
        "pdf_path": preview_path
    }
