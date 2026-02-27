import json
from pathlib import Path
from uuid import uuid4

from legalchat.services.embedding import get_embedding
from legalchat.services.endee_client import create_index, add_vectors

BASE_DIR = Path("legalchat/data")
ARTICLES_DIR = BASE_DIR / "constitution_articles"
CASES_DIR = BASE_DIR / "cases"
STATUTES_DIR = BASE_DIR / "statutes"


def load_documents():
    documents = []

    # Constitution Articles
    for file in ARTICLES_DIR.glob("article_*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        documents.append({
            "text": data["text"],
            "metadata": {
                "type": "constitution",
                "identifier": f"Article {data['article']}",
                "title": data["title"],
                "source": data["source"]
            }
        })

    # Judgments
    for file in CASES_DIR.glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        documents.append({
            "text": data["text"],
            "metadata": {
                "type": "judgment",
                "identifier": data["case_name"],
                "court": data["court"],
                "source": data["source"]
            }
        })

    # Statutes
    for file in STATUTES_DIR.glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        statute_name = data["name"]

        for section_no, section_text in data["sections"].items():
            documents.append({
                "text": section_text,
                "metadata": {
                    "type": "statute",
                    "identifier": f"Section {section_no}",
                    "statute": statute_name,
                    "source": data["source"]
                }
            })

    return documents


def ingest():
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    # Detect embedding dimension
    test_vec = get_embedding("test")
    dimension = len(test_vec)

    print(f"Detected embedding dimension: {dimension}")

    # Create index
    create_index(dimension)

    vectors = []

    for i, doc in enumerate(docs):
        embedding = get_embedding(doc["text"])

        vectors.append({
            "id": str(uuid4()),
            "values": embedding,
            "metadata": {
                **doc["metadata"],
                "doc_index": i
            }
        })

    # Push to Endee
    add_vectors(vectors)

    print("Endee ingestion complete.")


if __name__ == "__main__":
    ingest()
