import json
from pathlib import Path
import requests
import os
from uuid import uuid4
from openai import OpenAI  # or your embedding provider

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = Path("legalchat/data")
ARTICLES_DIR = BASE_DIR / "constitution_articles"
CASES_DIR = BASE_DIR / "cases"
STATUTES_DIR = BASE_DIR / "statutes"

ENDEE_BASE_URL = "http://localhost:8080"
INDEX_NAME = "legal_index"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# HELPER: Create Index
# -----------------------------
def create_index(dimension=1536):
    response = requests.post(
        f"{ENDEE_BASE_URL}/api/v1/index/create",
        json={
            "index_name": INDEX_NAME,
            "dimension": dimension
        }
    )
    print("Index response:", response.text)


# -----------------------------
# HELPER: Generate Embedding
# -----------------------------
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# -----------------------------
# LOAD DOCUMENTS
# -----------------------------
documents = []
metadata_list = []

# Constitution Articles
for file in ARTICLES_DIR.glob("article_*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    documents.append(data["text"])
    metadata_list.append({
        "type": "constitution",
        "identifier": f"Article {data['article']}",
        "title": data["title"],
        "source": data["source"]
    })

# Judgments
for file in CASES_DIR.glob("*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    documents.append(data["text"])
    metadata_list.append({
        "type": "judgment",
        "identifier": data["case_name"],
        "court": data["court"],
        "source": data["source"]
    })

# Statutes
for file in STATUTES_DIR.glob("*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))
    statute_name = data["name"]

    for section_no, section_text in data["sections"].items():
        documents.append(section_text)
        metadata_list.append({
            "type": "statute",
            "identifier": f"Section {section_no}",
            "statute": statute_name,
            "source": data["source"]
        })

print(f"📚 Total documents loaded: {len(documents)}")


# -----------------------------
# INGEST INTO ENDEE
# -----------------------------
def ingest():
    vectors_payload = []

    for text, meta in zip(documents, metadata_list):
        embedding = get_embedding(text)

        vectors_payload.append({
            "id": str(uuid4()),
            "values": embedding,
            "metadata": {
                **meta,
                "text": text
            }
        })

    response = requests.post(
        f"{ENDEE_BASE_URL}/api/v1/vector/add",
        json={
            "index_name": INDEX_NAME,
            "vectors": vectors_payload
        }
    )

    print("Ingestion response:", response.text)


if __name__ == "__main__":
    create_index()
    ingest()
    print("✅ Endee ingestion complete")
