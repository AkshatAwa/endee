import os
import json
import re
import requests
from pathlib import Path
from PyPDF2 import PdfReader

# --------------------------------------
# CONFIG: STATUTE PDFs & OUTPUT
# --------------------------------------
PDF_DIR = Path("pdfs")
STATUTE_DIR = Path("statutes")
PDF_DIR.mkdir(exist_ok=True)
STATUTE_DIR.mkdir(exist_ok=True)

STATUTES = {
    "Indian_Contract_Act_1872": {
        "url": "https://www.indiacode.nic.in/bitstream/123456789/2187/2/A187209.pdf",
        "min_sections": 170
    },
    "Indian_Evidence_Act_1872": {
        "url": "https://www.indiacode.nic.in/bitstream/123456789/15351/1/iea_1872.pdf",
        "min_sections": 160
    },
    "Code_of_Criminal_Procedure_1973": {
        "url": "https://www.indiacode.nic.in/bitstream/123456789/15272/1/the_code_of_criminal_procedure%2C_1973.pdf",
        "min_sections": 460
    },
    "Code_of_Civil_Procedure_1908": {
        "url": "https://sclsc.gov.in/theme/front/pdf/ACTS%20FINAL/THE%20CODE%20OF%20CIVIL%20PROCEDURE%2C%201908.pdf",
        "min_sections": 150
    },
    "Companies_Act_2013": {
        "url": "https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf",
        "min_sections": 450
    },
    "Industrial_Disputes_Act_1947": {
        "url": "https://www.indiacode.nic.in/bitstream/123456789/22042/1/a1947-14.pdf",
        "min_sections": 40
    }
}

# --------------------------------------
# UTILS: Download PDFs
# --------------------------------------
def download_pdf(name, url):
    pdf_path = PDF_DIR / f"{name}.pdf"
    if pdf_path.exists():
        print(f"📥 Already downloaded: {pdf_path}")
        return pdf_path

    print(f"📥 Downloading {name} ...")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    with open(pdf_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    print(f"✅ Saved PDF: {pdf_path}")
    return pdf_path

# --------------------------------------
# UTILS: Extract Sections from PDF text
# --------------------------------------
def extract_sections_from_text(text):
    sections = {}
    current = None
    buffer = []

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        # Strong section start detection
        match = re.match(r"^(\d{1,3}[A-Z]?)\.\s*(.+)", line)

        if match:
            # save previous section
            if current and len(" ".join(buffer)) > 100:
                sections[current] = " ".join(buffer).strip()

            current = match.group(1)
            buffer = [match.group(2)]

        else:
            # Handle cases where section number is merged
            inline_match = re.match(r".*?(\d{1,3}[A-Z]?)\.\s+([A-Z].+)", line)
            if inline_match:
                if current and len(" ".join(buffer)) > 100:
                    sections[current] = " ".join(buffer).strip()

                current = inline_match.group(1)
                buffer = [inline_match.group(2)]
            else:
                if current:
                    buffer.append(line)

    if current and len(" ".join(buffer)) > 100:
        sections[current] = " ".join(buffer).strip()

    return sections

# --------------------------------------
# MAIN
# --------------------------------------
for name, info in STATUTES.items():
    # 1. Download
    pdf_path = download_pdf(name, info["url"])

    # 2. Read PDF text
    reader = PdfReader(str(pdf_path))
    full_text = ""
    for page in reader.pages:
        pg_text = page.extract_text()
        if pg_text:
            full_text += pg_text + "\n"

    # 3. Extract sections
    print(f"📄 Parsing sections for {name} ...")
    sections = extract_sections_from_text(full_text)

    # 4. Basic validation
    if len(sections) < info["min_sections"]:
        raise RuntimeError(
            f"❌ Incomplete parse for {name} "
            f"(got {len(sections)}, expected {info['min_sections']}+)"
        )

    # 5. Write JSON
    statute_json = {
        "type": "statute",
        "name": name.replace("_", " "),
        "source": "Official PDF (Legislative Department / India Code)",
        "sections": sections
    }

    output_file = STATUTE_DIR / f"{name}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(statute_json, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON saved: {output_file}")
    print(f"📌 Sections extracted: {len(sections)}")

print("\n🎯 STATUTE JSON GENERATION COMPLETE")
