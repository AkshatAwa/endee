# SwaRakshak 2.0  
### Endee-Powered Retrieval-Augmented Legal Intelligence System

SwaRakshak 2.0 is a modular Legal AI backend built on a Retrieval-Augmented Generation (RAG) architecture.

The system integrates the **Endee Vector Database** as the core semantic retrieval engine and uses **local embeddings via Ollama** to provide a fully self-contained, scalable, AI-native legal intelligence pipeline.

The architecture is designed for structured legal reasoning across constitutional provisions, statutory law, and landmark judicial precedents.

---

## Evaluation Compliance

This project is implemented inside a fork of the official Endee repository as required by the internship guidelines.

**Forked Repository Base:**  
https://github.com/AkshatAwa/endee  

Project Location Inside Fork:  
```
projects/swarakshak/
```

Endee is used as the exclusive vector indexing and semantic retrieval engine.

No alternative vector database is used.

---

## Executive Summary

Traditional legal search systems rely on keyword matching, which fails in semantic reasoning tasks.

SwaRakshak 2.0 addresses this limitation by combining:

- Local dense embeddings  
- Endee high-performance vector indexing  
- Structured metadata validation  
- Context-injected generation  

This ensures legally grounded, citation-backed AI responses.

---

## System Architecture

The system follows a layered Retrieval-Augmented Generation pipeline:

```
User Query
↓
Query Normalization
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
```

All model outputs are grounded in retrieved legal authority.

---

## Core Architectural Components

| Component            | Technology                  | Responsibility |
|---------------------|----------------------------|---------------|
| Embedding Layer     | Ollama (mxbai-embed-large) | Dense vector generation |
| Vector Database     | Endee                      | High-performance similarity search |
| Retrieval Engine    | Custom ranking logic       | Citation validation & filtering |
| Generator Module    | Context-aware reasoning    | Structured legal output |
| API Layer           | FastAPI                    | Endpoint exposure |

---

## Endee Integration Details

**Index Creation Endpoint**
```
POST /api/v1/index/create
```

**Vector Ingestion Endpoint**
```
POST /api/v1/vector/add
```

**Vector Search Endpoint**
```
POST /api/v1/vector/search
```

All semantic retrieval operations are executed exclusively through Endee’s vector search API.

---

## Vector Index Specifications

- Embedding Model: mxbai-embed-large  
- Embedding Execution: Local via Ollama  
- Embedding Dimension: Auto-detected at ingestion  
- Distance Metric: L2 (Endee default)  
- Top-K Retrieval: 20 (configurable)  
- Metadata Filtering: Section-level validation layer  

---

## Retrieval Intelligence

The retrieval engine includes:

- Domain classification (contract, employment, labour, constitutional)
- Section-level validation
- Semantic scoring based on vector distance
- Declaratory provision detection
- Top-K citation filtering

This ensures legal precision and prevents irrelevant retrieval.

---

## Legal Corpus Coverage

Structured ingestion supports:

- Constitutional Articles
- Landmark Supreme Court Judgments
- Statutory Provisions (Section-wise JSON)

Each document stores metadata including:

- Document type
- Identifier (Article / Section / Case Name)
- Statute reference
- Source attribution

---

## Project Structure

```
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
```

Architecture enforces strict separation between:

- Embedding logic  
- Vector database integration  
- Retrieval logic  
- Generation logic  
- API exposure  

---

## Technology Stack

| Layer         | Technology |
|--------------|-----------|
| Backend      | Python |
| API          | FastAPI |
| Vector DB    | Endee |
| Embeddings   | Ollama (mxbai-embed-large) |
| Deployment   | Docker |
| Data Format  | JSON (Structured Legal Corpus) |

---

## Deployment & Execution Guide

### 1. Start Ollama

```
ollama serve
ollama pull mxbai-embed-large
```

### 2. Start Endee Vector Database

```
docker run -p 8080:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest
```

### 3. Ingest Legal Corpus into Endee

```
python legalchat/services/endee_ingest.py
```

This step:
- Generates embeddings  
- Creates Endee index  
- Uploads vectors with metadata  

### 4. Start Backend API

```
uvicorn legalchat.api.main:app --reload
```

---

## Example Query

**Query:**  
_Is Right to Privacy a fundamental right in India?_

System Flow:

1. Query normalized
2. Local embedding generated
3. Semantic similarity search executed in Endee
4. Relevant constitutional provisions retrieved
5. Context injected into generator
6. Structured explanation returned

---

## Architectural Rationale

Legal reasoning depends on semantic similarity rather than lexical overlap.

Vector indexing enables:

- Context-aware retrieval
- Cross-document reasoning
- Scalable AI-native backend systems

Endee provides efficient high-dimensional indexing required for such workloads.

---

## Performance Characteristics

- Corpus Size: ~500+ structured legal documents  
- Embedding Execution: Local  
- Vector Retrieval: Real-time semantic search  
- Deployment: Docker-isolated Endee runtime  
- No dependency on external embedding APIs  

---

## Security & Operational Design

- Local embedding execution  
- No mandatory external API keys  
- Environment-based configuration  
- Modular service isolation  
- Reproducible Docker deployment  

---

## Future Enhancements

- Hybrid Search (Semantic + Lexical Fusion)  
- Confidence scoring mechanism  
- Multi-document PDF ingestion  
- Domain fine-tuned legal embeddings  
- Agentic AI workflow integration  

---

## Disclaimer

This project is developed for educational and research purposes only and does not constitute legal advice.

---

## Author

Akshat Awasthi  
AI/ML Engineer  
Legal AI Systems | Vector-Based Architectures
