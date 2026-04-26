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

The QA Expert Agent behaves like a Senior QA Engineer with 15+ years of experience mentoring a junior tester. Ask a question, and the system searches the vector store, retrieves the most relevant ISTQB chunks, and passes them to a local LLM to generate a structured answer.

**Response format (5-part model):**

- **Definition** — ISTQB concept explanation
- **Real project example** — practical usage
- **Suggested test cases** — actionable tests
- **Common mistakes** — pitfalls
- **Interview explanation** — how to explain in interviews

The agent cites retrieved chunks with inline `[page N]` markers and a References block. It abstains when retrieval evidence is too weak (similarity score below threshold) rather than hallucinating.

Run `qa-agent ingest <pdf>` to load a document, then `qa-agent ask "<question>"` to query it.

**Known limitation:** The current model (`smollm2-360m`, 360M params) is too small for reliable structured output. Answers may not consistently follow the five-part format or citation rules. The Step 10 golden test suite documents this with measurements. A future model upgrade to a 3B+ instruct model would significantly improve answer quality.

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

```bash
poetry run qa-agent ask "What is metamorphic testing?"
```

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

```bash
poetry run pytest tests/golden/ -v
```

Evaluates ≥10 ISTQB Q&A pairs on concept correctness, terminology coverage, and hallucination absence. Results are informative — the current model (`smollm2-360m`) is too small for reliable structured output, and pass rate will reflect that honestly.

---

## Why No AI Frameworks?

This project intentionally avoids LangChain, LlamaIndex, CrewAI, AutoGen, and LangGraph.

The goal is to understand how RAG systems work internally — not to wrap a framework.

---

## Roadmap

| Phase | Status        | Description                              |
|-------|---------------|------------------------------------------|
| 1     | Final         | QA Expert Agent — full RAG pipeline with grounded answers, citation enforcement, abstain on weak evidence (Steps 1–9 complete; Step 10 golden evaluation in progress) |

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
