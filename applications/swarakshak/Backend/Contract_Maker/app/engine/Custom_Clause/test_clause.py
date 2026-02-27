import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from Backend.Contract_Maker.app.engine.Custom_Clause.clause_pipeline import process_user_prompt

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../")
)

NDA_JSON_PATH = os.path.join(
    BASE_DIR, "Contract_Maker", "app", "templates", "Doc_json",
    "Non_Disclosure_Agreement.json"
)

OUTPUT_JSON_PATH = os.path.join(
    BASE_DIR, "Contract_Maker", "app", "templates", "Doc_json",
    "Non_Disclosure_Updated.json"
)

OUTPUT_PDF_PATH = os.path.join(
    BASE_DIR, "Contract_Maker", "app", "engine", "Custom_Clause",
    "output", "nda", "nda_final.pdf"
)

os.makedirs(os.path.dirname(OUTPUT_PDF_PATH), exist_ok=True)


def generate_pdf_from_json(nda_json: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, nda_json.get("title", "NON-DISCLOSURE AGREEMENT"))
    y -= 40

    c.setFont("Times-Roman", 11)

    for clause in nda_json.get("clauses", []):
        title = clause.get("title", "")
        text = clause.get("text", "")

        c.setFont("Times-Bold", 11)
        c.drawString(40, y, title)
        y -= 18

        c.setFont("Times-Roman", 11)
        for line in text.split(". "):
            c.drawString(40, y, line.strip())
            y -= 15
            if y < 50:
                c.showPage()
                c.setFont("Times-Roman", 11)
                y = height - 50

        y -= 10

    c.save()


def main():
    # 1️⃣ Load NDA JSON
    with open(NDA_JSON_PATH, "r", encoding="utf-8") as f:
        nda_json = json.load(f)

    print("\n📝 Enter NDA clause requirement:")
    user_prompt = input("> ")

    # 2️⃣ Process through full pipeline
    result = process_user_prompt(user_prompt, nda_json)

    print("\n🧠 RESULT:")
    print(result)

    if result["status"] != "added":
        print("\n❌ Clause rejected. Nothing generated.")
        return

    # 3️⃣ Save updated JSON
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(nda_json, f, indent=2)

    # 4️⃣ Generate PDF
    generate_pdf_from_json(nda_json, OUTPUT_PDF_PATH)

    print("\n✅ SUCCESS")
    print(f"📄 Updated JSON: {OUTPUT_JSON_PATH}")
    print(f"📑 Generated PDF: {OUTPUT_PDF_PATH}")


if __name__ == "__main__":
    main()
