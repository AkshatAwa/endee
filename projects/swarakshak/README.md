# SwaRakshak 2.0  
## Endee-Powered Retrieval-Augmented Legal Intelligence System

SwaRakshak 2.0 is a modular Legal AI backend built on a Retrieval-Augmented Generation (RAG) architecture.

The system integrates the **Endee Vector Database** for high-performance semantic retrieval and uses a **local embedding model via Ollama** to enable a fully self-contained, scalable, AI-native legal intelligence pipeline.

The architecture is designed for structured legal reasoning across constitutional provisions, statutory law, and landmark judicial precedents.

---

# Executive Summary

SwaRakshak 2.0 solves a core limitation in legal AI systems: keyword-based search is insufficient for semantic reasoning.

By combining:

- Local dense embeddings  
- Endee high-performance vector indexing  
- Structured metadata filtering  
- Context-injected generation  

The system ensures legally grounded, citation-backed AI responses.

---

# System Architecture

The system follows a layered Retrieval-Augmented Generation pipeline:

User Query  
↓  
Query Normalization Layer  
↓  
Local Embedding Generation (Ollama – mxbai-embed-large)  
↓  
Endee Vector Database (Semantic Similarity Search)  
↓  
Top-K Context Retrieval  
↓  
Context Injection into Generator  
↓  
Structured Legal Response  

This guarantees that model outputs are grounded in retrieved legal authority.

---

# Core Architectural Components

| Component | Description | Responsibility |
|------------|------------|----------------|
| Embedding Layer | Local embedding via Ollama | Converts text into dense vectors |
| Endee Vector DB | High-performance vector search | Stores & retrieves embeddings |
| Retrieval Engine | Semantic ranking + validation | Filters and scores citations |
| Generator Module | Context-aware reasoning | Produces structured legal output |
| API Layer | FastAPI backend | Exposes endpoints |

---

# Embedding Layer

- Model: `mxbai-embed-large`
- Executed locally via Ollama
- No dependency on OpenAI or external embedding APIs
- Deterministic embedding dimension for index consistency

---

# Endee Vector Database

- High-dimensional vector storage
- Efficient similarity search
- Metadata-backed citation filtering
- Docker-based deployment
- Designed for scalable semantic workloads

---

# Retrieval Intelligence

The retrieval engine includes:

- Domain classification (contract, employment, labour, constitutional)
- Section-level validation
- Semantic scoring based on vector distance
- Declaratory provision detection
- Top-k citation filtering

This ensures legal accuracy and prevents irrelevant retrieval.

---

# Legal Corpus Coverage

The system supports structured ingestion of:

- Constitutional Articles
- Landmark Supreme Court Judgments
- Statutory Provisions (Section-wise structured JSON)

Each document is stored with metadata including:

- Document type
- Identifier (Article / Section / Case Name)
- Statute reference
- Source attribution

---

# Project Structure

Backend/  
├── legalchat/  
│   ├── api/  
│   ├── services/  
│   ├── data/  
│   ├── memory/  
│  
├── LegalAPI/  
├── Contract_Maker/  
├── requirements.txt  
└── .env.example  

Frontend/  
└── UI Layer  

The architecture enforces strict separation between:

- Embedding logic  
- Vector database integration  
- Retrieval logic  
- Generation logic  
- API exposure  

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | Python |
| API | FastAPI |
| Vector Database | Endee |
| Embeddings | Ollama (mxbai-embed-large) |
| Deployment | Docker |
| Data Format | JSON (Structured Legal Corpus) |

---

# Deployment & Execution Guide

## 1. Start Ollama

    ollama serve
    ollama pull mxbai-embed-large

---

## 2. Start Endee Vector Database

    docker run -p 8080:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest

---

## 3. Ingest Legal Corpus into Endee

    python legalchat/services/endee_ingest.py

This step:
- Generates embeddings
- Creates Endee index
- Uploads vectors with metadata

---

## 4. Start Backend API

    uvicorn legalchat.api.main:app --reload

---

# Example Query Execution

Query:

    Is Right to Privacy a fundamental right in India?

System Flow:

1. Query rewritten into legal terminology  
2. Embedding generated locally  
3. Semantic similarity search executed in Endee  
4. Relevant constitutional provisions retrieved  
5. Context injected into generator  
6. Structured explanation returned  

---

# Why Vector-Based Legal Retrieval?

Traditional databases fail in legal reasoning because:

- Legal meaning depends on semantic similarity  
- Context matters more than keyword overlap  
- Cross-document reasoning is required  

Endee enables:

- High-dimensional similarity indexing  
- Efficient retrieval at scale  
- AI-native backend design  

---

# Security & Operational Design

- No mandatory external embedding APIs
- Local embedding execution
- Environment-based configuration
- Modular service separation
- Reproducible Docker-based deployment

---

# Future Enhancements

- Hybrid Search (Semantic + Lexical Fusion)
- Confidence scoring system
- Multi-document PDF ingestion
- Domain fine-tuned legal embeddings
- Agentic AI workflow integration

---

# Disclaimer

This project is developed for educational and research purposes only and does not constitute legal advice.

---

# Author

Akshat Awasthi  
AI/ML Engineer  
Legal AI Systems | Vector-Based Architectures
