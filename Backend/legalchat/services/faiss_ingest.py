import json
from pathlib import Path
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

BASE_DIR = Path("legalchat/data")
ARTICLES_DIR = BASE_DIR / "constitution_articles"
CASES_DIR = BASE_DIR / "cases"
STATUTES_DIR = BASE_DIR / "statutes"

STORE_DIR = Path("legalchat/faiss_store")
STORE_DIR.mkdir(exist_ok=True)

documents = []
metadata = []

# -------------------------------------------------
# LOAD CONSTITUTION ARTICLES
# -------------------------------------------------
for file in ARTICLES_DIR.glob("article_*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    documents.append(data["text"])
    metadata.append({
        "type": "constitution",
        "identifier": f"Article {data['article']}",
        "title": data["title"],
        "source": data["source"]
    })

# -------------------------------------------------
# LOAD JUDGMENTS
# -------------------------------------------------
for file in CASES_DIR.glob("*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    documents.append(data["text"])
    metadata.append({
        "type": "judgment",
        "identifier": data["case_name"],
        "court": data["court"],
        "source": data["source"]
    })

# -------------------------------------------------
# LOAD STATUTES (SECTION-WISE)
# -------------------------------------------------
for file in STATUTES_DIR.glob("*.json"):
    data = json.loads(file.read_text(encoding="utf-8"))

    statute_name = data["name"]

    for section_no, section_text in data["sections"].items():
        documents.append(section_text)
        metadata.append({
            "type": "statute",
            "identifier": f"Section {section_no}",
            "statute": statute_name,
            "source": data["source"]
        })

print(f"📚 Total documents loaded: {len(documents)}")

# -------------------------------------------------
# TF-IDF VECTORIZATION
# -------------------------------------------------
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=8000
)

X = vectorizer.fit_transform(documents)
X = X.astype(np.float32).toarray()

# -------------------------------------------------
# FAISS INDEX
# -------------------------------------------------
dimension = X.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(X)

# -------------------------------------------------
# SAVE EVERYTHING
# -------------------------------------------------
faiss.write_index(index, str(STORE_DIR / "index.faiss"))

with open(STORE_DIR / "metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

with open(STORE_DIR / "vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open(STORE_DIR / "documents.pkl", "wb") as f:
    pickle.dump(documents, f)


print("✅ FAISS ingestion complete (constitution + judgments + statutes)")
