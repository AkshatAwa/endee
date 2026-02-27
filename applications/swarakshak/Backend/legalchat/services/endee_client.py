import requests

ENDEE_BASE_URL = "http://localhost:8080"
INDEX_NAME = "legal_index"

def create_index(dimension: int):
    requests.post(
        f"{ENDEE_BASE_URL}/api/v1/index/create",
        json={
            "index_name": INDEX_NAME,
            "dimension": dimension
        }
    )

def add_vectors(vectors: list):
    requests.post(
        f"{ENDEE_BASE_URL}/api/v1/vector/add",
        json={
            "index_name": INDEX_NAME,
            "vectors": vectors
        }
    )

def search(vector: list, top_k: int = 5):
    res = requests.post(
        f"{ENDEE_BASE_URL}/api/v1/vector/search",
        json={
            "index_name": INDEX_NAME,
            "vector": vector,
            "top_k": top_k
        }
    )
    res.raise_for_status()
    return res.json().get("results", [])
