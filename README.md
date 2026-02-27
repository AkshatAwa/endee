SwaRakshak 2.0
Endee-Powered Retrieval-Augmented Legal Intelligence System

SwaRakshak 2.0 is a modular Legal AI backend built on a Retrieval-Augmented Generation (RAG) architecture.

The system leverages the Endee Vector Database for high-performance semantic retrieval and uses a local embedding model via Ollama to enable a fully self-contained, scalable, AI-native legal intelligence pipeline.

The architecture is designed for structured legal reasoning over constitutional provisions, statutory law, and landmark judicial precedents.

1. Problem Context

Legal knowledge systems face several structural challenges:

High semantic complexity in statutory language

Context-sensitive interpretation requirements

Inefficiency of keyword-based search mechanisms

Lack of evidence-backed AI reasoning systems

Traditional relational or lexical search approaches are insufficient for semantic legal analysis.

SwaRakshak 2.0 addresses these limitations using vector-based semantic retrieval integrated with contextual generation.

2. System Architecture

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

This architecture ensures that generation is grounded in retrieved legal authority rather than free-form model output.

3. Core Architectural Components
3.1 Embedding Layer

Local embedding model: mxbai-embed-large

Executed via Ollama

No dependency on external embedding APIs

Deterministic vector dimension for index consistency

3.2 Endee Vector Database

High-dimensional vector indexing

Efficient similarity-based retrieval

Metadata-backed citation filtering

Docker-based deployment

Endee serves as the semantic backbone of the retrieval system.

3.3 Retrieval Engine

Domain classification (contract, employment, labour, constitutional, etc.)

Statute validation and section-level verification

Semantic distance scoring

Declaratory provision detection

Top-k citation filtering

3.4 Generation Layer

Context-aware legal explanation

Structured, evidence-backed response format

Modular separation from retrieval logic

3.5 API Layer

FastAPI-based backend

Modular endpoint architecture

Clean separation of services

4. Legal Corpus Structure

The system supports structured ingestion of:

Constitutional Articles

Landmark Supreme Court Judgments

Statutory Provisions (Section-wise structured JSON)

Each document is embedded, indexed in Endee, and stored with structured metadata including:

Document type

Identifier (Article / Section / Case Name)

Statute reference

Source attribution

5. Project Structure

Backend/
├── legalchat/
│ ├── api/
│ ├── services/
│ ├── data/
│ ├── memory/
│
├── LegalAPI/
├── Contract_Maker/
├── requirements.txt
└── .env.example

Frontend/
└── UI Layer

The system maintains strict modular separation between:

Embedding logic

Vector database client

Retrieval layer

Generation logic

API endpoints

6. Technology Stack

Python

FastAPI

Endee Vector Database

Ollama (Local Embeddings)

Docker

JSON-based structured legal corpus

Modular RAG architecture

7. Deployment and Execution
Step 1: Start Ollama
ollama serve
ollama pull mxbai-embed-large
Step 2: Start Endee
docker run -p 8080:8080 -v endee-data:/data --name endee-server endeeio/endee-server:latest
Step 3: Ingest Legal Data
python legalchat/services/endee_ingest.py

This step:

Generates embeddings

Creates Endee index

Uploads vectors with metadata

Step 4: Run Backend API
uvicorn legalchat.api.main:app --reload
8. Example Query Flow

Example Query:

"Is Right to Privacy a fundamental right in India?"

Execution Steps:

Query normalized into structured legal terms

Embedding generated locally

Semantic similarity search executed in Endee

Relevant constitutional provisions and judgments retrieved

Context injected into generation layer

Structured legal explanation returned with citations

9. Design Rationale

Vector-based retrieval is essential for legal reasoning systems because:

Legal language relies on semantic similarity rather than keyword overlap

Contextual interpretation requires cross-document reasoning

Scalable legal intelligence requires high-dimensional vector indexing

Endee provides an optimized, production-grade vector database that supports this architecture efficiently.

10. Security and Operational Considerations

No mandatory external embedding API dependency

Local embedding execution via Ollama

Environment-based configuration management

Modular and extensible service architecture

Clean separation between ingestion, retrieval, and generation layers

11. Future Enhancements

Hybrid retrieval (lexical + semantic fusion)

Confidence scoring mechanism

Multi-document PDF ingestion pipeline

Fine-tuned domain-specific legal embeddings

Agentic AI workflow integration

Disclaimer

This system is developed for educational and research purposes and does not constitute legal advice.

Author

Akshat Awasthi
AI/ML Engineer
Legal AI Systems | Vector-Based Architectures
