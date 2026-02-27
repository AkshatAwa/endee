from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_nda_pdf(nda_json: dict, output_path: str):
    pdf = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>NON-DISCLOSURE AGREEMENT</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    # NDA Clauses
    for clause in nda_json.get("clauses", []):
        title = clause.get("title")
        text = clause.get("text", "")

        if title:
            story.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))
            story.append(Spacer(1, 8))

        for para in text.split("\n"):
            story.append(Paragraph(para, styles["Normal"]))
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 14))

    # 🔽 SIGNATURE SECTION (ADDED)
    story.append(Spacer(1, 40))

    story.append(Paragraph("<b>DISCLOSING PARTY</b>", styles["Heading3"]))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Signature _________________________________________________", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Typed or Printed Name ___________________________ Date: _______________", styles["Normal"]))

    story.append(Spacer(1, 40))

    story.append(Paragraph("<b>RECEIVING PARTY</b>", styles["Heading3"]))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Signature _________________________________________________", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Typed or Printed Name ___________________________ Date: _______________", styles["Normal"]))

    pdf.build(story)
