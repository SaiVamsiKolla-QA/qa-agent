# QA Expert Agent (ISTQB Mentor)

A local AI agent that turns ISTQB certification material into an interactive QA mentor.

The agent answers software testing questions, explains testing concepts, and suggests practical test cases — grounded only in retrieved ISTQB documentation.

This project is intentionally built from primitives (without LangChain or orchestration frameworks) to understand how Retrieval-Augmented Generation (RAG) and AI agents actually work.

The system runs fully locally using mimik AI Foundation with models served via the mimoe runtime.

---

## ⚠️ AI Development Rules

This repository contains a `CLAUDE.md` file designed for use with Claude Code.

It defines strict development rules for AI-assisted coding sessions, including:

- One deliverable per step
- Mandatory review checkpoints
- Small, testable increments
- No hidden abstractions

If you plan to contribute or use Claude Code with this repository, read `CLAUDE.md` first.

---

## Project Goals

This project exists for three main purposes.

### 1. Learn AI Engineering Fundamentals

Build an AI system from the ground up by implementing:

- Retrieval Augmented Generation (RAG)
- Document chunking
- Embeddings
- Vector search
- Agent orchestration
- Prompt design

All components are implemented without high-level AI frameworks.

### 2. Improve QA Expertise

The system turns ISTQB study material into an interactive QA mentor. It helps:

- Explain testing concepts
- Generate realistic test ideas
- Practice interview explanations
- Reinforce ISTQB terminology

### 3. Build a Portfolio Project

This repository demonstrates skills in:

- Python engineering
- AI agent systems
- Local LLM workflows
- RAG architectures
- QA domain expertise

---

## What the Agent Does

### Currently working (Steps 1–8b)

The ingestion pipeline loads ISTQB PDFs, splits them into overlapping chunks, generates embeddings with `sentence-transformers/all-MiniLM-L6-v2`, and stores them in ChromaDB with provenance metadata (source document, page number, chunk index, stable chunk ID). The vector store can be queried semantically via the Python API.

Run `qa-agent ingest <pdf>` to load a document. The collection is replaced on each ingest run.

### In development (Step 9)

The QA Expert Agent will behave like a Senior QA Engineer with 15+ years of experience mentoring a junior tester. When you ask a question, the system will search the vector store, retrieve the most relevant chunks, and pass them to a local LLM to generate a structured answer.

**Planned response format (5-part model):**

- **Definition** — ISTQB concept explanation
- **Real project example** — practical usage
- **Suggested test cases** — actionable tests
- **Common mistakes** — pitfalls
- **Interview explanation** — how to explain in interviews

The agent will cite retrieved chunks and abstain from answering when retrieval evidence is too weak.

---

## Architecture

The system follows a standard Retrieval-Augmented Generation (RAG) architecture.

### Ingestion Pipeline

```
PDF
↓
pdf_loader
↓
chunker
↓
embeddings
↓
vector_store.add_chunks()
```

Steps:

1. Load ISTQB PDF
2. Split text into chunks
3. Generate embeddings
4. Store vectors in ChromaDB

### Query Pipeline

```
User Question
↓
CLI
↓
QA Expert Agent
↓
Vector Search
↓
Local LLM (mimik runtime)
↓
Answer with citations
```

---

## Technology Stack

| Component       | Technology                            |
|-----------------|---------------------------------------|
| Language        | Python 3.13                           |
| Package Manager | Poetry                                |
| LLM Runtime     | mimik AI Foundation                   |
| Model Serving   | mimoe                                 |
| Embeddings      | sentence-transformers/all-MiniLM-L6-v2|
| Vector Database | ChromaDB                              |
| PDF Parsing     | pypdf                                 |
| Configuration   | pydantic-settings                     |
| Testing         | pytest                                |
| Linting         | ruff                                  |
| Interface       | CLI                                   |

The local LLM is accessed via:

```
http://localhost:8083/mimik-ai/openai/v1/chat/completions
```

---

## Repository Structure

```
qa-expert-agent/
│
├── qa_agent/
│   ├── cli.py
│   ├── config.py
│   ├── llm_client.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── pdf_loader.py
│   ├── chunker.py
│   │
│   ├── prompts/               (Step 9)
│   │
│   └── agents/                (Step 9)
│
├── data/
│   └── istqb_docs/
│
├── chroma_db/
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── pyproject.toml
├── .env.example
├── CLAUDE.md
├── TODO.md
└── README.md
```

---

## Quick Start

### Requirements

- Python 3.13
- Poetry 2.x
- mimik AI Foundation runtime
- VS Code

The mimik runtime must be running on `http://localhost:8083`.

### First-time Setup

```bash
git clone https://github.com/SaiVamsiKolla-QA/qa-agent.git
cd qa-expert-agent
poetry install
cp .env.example .env
```

Edit `.env` and set `MODEL_NAME` to the model name reported by your mimik runtime.

### Start the Runtime

```bash
mimoe start
mimoe status
```

### Connectivity Test

```bash
poetry run qa-agent ping
```

Expected output:

```
mimik reachable. model reply: ...
```

### Ingest ISTQB Material

Place PDFs in `data/istqb_docs/`, then run:

```bash
poetry run qa-agent ingest data/istqb_docs/<filename>.pdf
```

### Ask Questions

Step 9 will add a `qa-agent ask` command for grounded QA answers — currently in development.

---

## Testing

### Unit Tests

```bash
poetry run pytest
```

### Integration Tests

```bash
poetry run pytest -m integration
```

### Golden RAG Tests

Step 10 will add a golden test suite at `tests/golden/` with ≥10 Q&A pairs evaluating concept correctness, ISTQB terminology coverage, and absence of hallucinations.

---

## Why No AI Frameworks?

This project intentionally avoids LangChain, LlamaIndex, CrewAI, AutoGen, and LangGraph.

The goal is to understand how RAG systems work internally — not to wrap a framework.

---

## Roadmap

| Phase | Status  | Description                              |
|-------|---------|------------------------------------------|
| 1     | Current | CLI ingest pipeline with provenance metadata (Steps 1–8b complete; Steps 9–10 in progress) |
| 2     | Planned | Test case generator agent (BVA, EP, decision tables) |
| 3     | Planned | QA interview coach with answer evaluation |
| 4     | Planned | FastAPI service + optional web UI        |

---

## Security

- No sensitive data stored
- ISTQB PDFs gitignored (`data/istqb_docs/`)
- Vector DB gitignored (`chroma_db/`)
- `.env` gitignored

---

## Author

Senior QA Engineer transitioning toward SDET → AI / ML Engineering.

Focus areas: AI agents, QA automation, RAG systems, Python engineering.

---

## License

MIT
