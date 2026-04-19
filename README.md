# QA Expert Agent (ISTQB Mentor)

A local AI agent that turns ISTQB certification material into an interactive QA mentor.

The agent answers software testing questions, explains testing concepts, and suggests practical test cases — grounded only in retrieved ISTQB documentation.

This project is intentionally built from primitives (without LangChain or orchestration frameworks) to understand how Retrieval-Augmented Generation (RAG) and AI agents actually work.

The system runs fully locally using :contentReference[oaicite:0]{index=0} with models served via the mimoe runtime.

---

# ⚠️ AI Development Rules

This repository contains a `CLAUDE.md` file designed for use with :contentReference[oaicite:1]{index=1}.

It defines strict development rules for AI-assisted coding sessions, including:

- One deliverable per step  
- Mandatory review checkpoints  
- Small, testable increments  
- No hidden abstractions  

If you plan to contribute or use Claude Code with this repository, read `CLAUDE.md` first.

---

# Project Goals

This project exists for three main purposes.

---

## 1. Learn AI Engineering Fundamentals

Build an AI system from the ground up by implementing:

- Retrieval Augmented Generation (RAG)
- Document chunking
- Embeddings
- Vector search
- Agent orchestration
- Prompt design

All components are implemented without high-level AI frameworks.

---

## 2. Improve QA Expertise

The system turns ISTQB study material into an interactive QA mentor.

It helps:

- Explain testing concepts
- Generate realistic test ideas
- Practice interview explanations
- Reinforce ISTQB terminology

---

## 3. Build a Portfolio Project

This repository demonstrates skills in:

- Python engineering
- AI agent systems
- Local LLM workflows
- RAG architectures
- QA domain expertise

---

# What the Agent Does

The QA Expert Agent behaves like a Senior QA Engineer with 15+ years of experience mentoring a junior tester.

When you ask a question, the system:

1. Searches ISTQB material stored in a vector database  
2. Retrieves the most relevant sections  
3. Sends the retrieved context to a local LLM  
4. Generates a structured explanation  

---

## Response Format (5-part model)

- Definition — ISTQB concept explanation  
- Real project example — practical usage  
- Suggested test cases — actionable tests  
- Common mistakes — pitfalls  
- Interview explanation — how to explain in interviews  

The agent cites retrieved context and avoids hallucinations.

---

# Architecture

The system follows a standard Retrieval-Augmented Generation (RAG) architecture.

---

## Ingestion Pipeline


PDF
↓
pdf_loader
↓
chunker
↓
embeddings
↓
vector_store.persist()


Steps:

- Load ISTQB PDF  
- Split text into chunks  
- Generate embeddings  
- Store vectors in ChromaDB  

---

## Query Pipeline


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


---

# Technology Stack

| Component | Technology |
|----------|-----------|
| Language | Python 3.13 |
| Package Manager | Poetry |
| LLM Runtime | :contentReference[oaicite:2]{index=2} |
| Model Serving | mimoe |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| PDF Parsing | pypdf |
| Configuration | pydantic-settings |
| Testing | pytest |
| Linting | ruff |
| Interface | CLI |

---

The local LLM is accessed via:


http://localhost:8083/mimik-ai/openai/v1/chat/completions


---

# Repository Structure


qa-agent/
│
├── qa_agent/
│ ├── cli.py
│ ├── config.py
│ ├── llm_client.py
│ ├── embeddings.py
│ ├── vector_store.py
│ ├── pdf_loader.py
│ ├── chunker.py
│ │
│ ├── prompts/
│ │ └── qa_expert.txt
│ │
│ └── agents/
│ └── qa_expert.py
│
├── data/
│ └── istqb_docs/
│
├── chroma_db/
│
├── tests/
│ ├── unit/
│ ├── integration/
│ └── golden/
│
├── pyproject.toml
├── .env.example
├── CLAUDE.md
├── TODO.md
└── README.md


---

# Quick Start

If mimik AI Foundation is running locally:

```bash
git clone https://github.com/SaiVamsiKolla-QA/qa-agent.git
cd qa-agent
poetry install
cp .env.example .env
Development Setup
Requirements
Python 3.13
Poetry 2.x
mimik AI Foundation runtime
VS Code

Runtime must be running on:

http://localhost:8083
First-time Setup
git clone https://github.com/SaiVamsiKolla-QA/qa-agent.git
cd qa-agent
poetry install
cp .env.example .env
Start Runtime
mimoe start
mimoe status
Connectivity Test
poetry run qa-agent ping

Expected:

mimik reachable. model reply: ...
Ingest ISTQB Material

Place PDFs in:

data/istqb_docs/

Run:

poetry run python -m qa_agent.ingest
Ask Questions
poetry run python -m qa_agent.cli

Example:

What is equivalence partitioning?
Testing Strategy
Unit Tests
pytest
Integration Tests
pytest -m integration
Golden RAG Tests

Validates:

correctness
terminology
no hallucinations
Why No AI Frameworks?

This project intentionally avoids:

LangChain
LlamaIndex
CrewAI
AutoGen
LangGraph

Reason:

To understand how RAG systems work internally.

Roadmap
Phase 1 (Current)
document ingestion
chunking
embeddings
vector search
CLI QA agent
Phase 2
test case generator agent
boundary analysis
decision tables
Phase 3
QA interview coach
answer evaluation
Phase 4
FastAPI service + optional UI
Security
No sensitive data stored
ISTQB PDFs ignored in Git
vector DB ignored
.env ignored
Author

Senior QA Engineer transitioning toward:

SDET → AI / ML Engineering

Focus areas:

AI agents
QA automation
RAG systems
Python engineering
License

MIT