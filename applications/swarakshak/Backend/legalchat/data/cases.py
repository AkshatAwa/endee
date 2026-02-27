from pathlib import Path
import json
import re

RAW_DIR = Path("/legalchat/data/raw_data")
OUT_DIR = Path("/legalchat/data/cases")

OUT_DIR.mkdir(parents=True, exist_ok=True)

CASES = {
    "kesavananda_bharati.txt": "Kesavananda Bharati Sripadagalvaru ... vs State Of Kerala And Anr on 24 April, 1973"
}

def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # remove page numbers
        if re.match(r"Page \d+", line):
            continue

        # remove obvious boilerplate
        if "Indian Kanoon" in line:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)

for filename, case_name in CASES.items():
    input_file = RAW_DIR / filename
    output_file = OUT_DIR / filename.replace(".txt", ".json")

    if not input_file.exists():
        print(f"⚠️ Missing file: {filename}")
        continue

    raw_text = input_file.read_text(encoding="utf-8", errors="ignore")
    cleaned_text = clean_text(raw_text)

    data = {
        "case_name": case_name,
        "court": "Supreme Court of India",
        "source": "Indian Kanoon (text extraction)",
        "text": cleaned_text
    }

    output_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"✅ Converted {filename} → {output_file.name}")

print("🎯 All cases converted successfully")
