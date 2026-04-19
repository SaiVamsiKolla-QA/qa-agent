# QA Expert Agent (ISTQB Mentor)

A local AI agent that turns **ISTQB certification material into an interactive QA mentor**.

The agent answers software testing questions, explains testing concepts, and suggests practical test cases — grounded only in retrieved ISTQB documentation.

This project is intentionally built **from primitives** (without LangChain or orchestration frameworks) to understand how **Retrieval-Augmented Generation (RAG)** and **AI agents** actually work.

The system runs **fully locally** using **mimik AI Foundation**.

---

# ⚠️ AI Development Rules

This repository contains a **`CLAUDE.md`** file designed for use with Claude Code.

It defines strict development rules for AI-assisted coding sessions, including:

- One deliverable per step
- Mandatory review checkpoints
- Small, testable increments
- No hidden abstractions

If you plan to contribute or use Claude Code with this repository, **read `CLAUDE.md` first.**

---

# Project Goals

This project exists for three main purposes.

## 1. Learn AI Engineering Fundamentals

Build an AI system from the ground up by implementing:

- Retrieval Augmented Generation (RAG)
- document chunking
- embeddings
- vector search
- agent orchestration
- prompt design

All components are implemented **without high-level AI frameworks**.

---

## 2. Improve QA Expertise

The system turns ISTQB study material into an **interactive QA mentor**.

It helps:

- explain testing concepts
- generate realistic test ideas
- practice interview explanations
- reinforce ISTQB terminology

---

## 3. Build a Portfolio Project

This repository demonstrates skills in:

- Python engineering
- AI agent systems
- local LLM workflows
- RAG architectures
- QA domain expertise

---

# What the Agent Does

The **QA Expert Agent** behaves like a **Senior QA Engineer with 15+ years of experience mentoring a junior tester.**

When you ask a question, the system:

1. Searches ISTQB material stored in a vector database
2. Retrieves the most relevant sections
3. Sends the retrieved context to a local LLM
4. Generates a structured explanation

Responses follow a **five-part QA explanation model**:

1. **Definition** — ISTQB concept explanation
2. **Real project example** — how it appears in real testing work
3. **Suggested test cases** — practical tests to run
4. **Common mistakes** — typical tester errors
5. **Interview explanation** — how to explain the concept in interviews

The agent **cites retrieved context** and avoids answering beyond available material.

---

# Architecture

The system follows a standard **Retrieval-Augmented Generation (RAG)** architecture.

Two pipelines power the system.

---

## Ingestion Pipeline

Runs once per document to prepare knowledge for retrieval.


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

1. Load ISTQB PDF
2. Split text into overlapping chunks
3. Generate embeddings for each chunk
4. Store vectors in ChromaDB

---

## Query Pipeline

Runs each time the user asks a question.


User question
↓
CLI
↓
QA Expert Agent
↓
Vector search
↓
LLM (mimik runtime)
↓
Answer with citations


---

# Technology Stack

| Component | Technology |
|---|---|
Language | Python 3.11+
Package Manager | Poetry
LLM Runtime | mimik AI Foundation
Model | GGUF instruct model (3B–7B)
Embeddings | sentence-transformers/all-MiniLM-L6-v2
Vector Database | ChromaDB
PDF Parsing | pypdf
Configuration | pydantic-settings
Testing | pytest
Linting | ruff
Interface | CLI

The LLM is accessed via an **OpenAI-compatible endpoint**:


http://localhost:8083/mimik-ai/openai/v1/chat/completions


---

# Repository Structure


qa-agent/
├── qa_agent/
│
│ ├── init.py
│ ├── cli.py
│ ├── config.py
│ ├── llm_client.py
│ ├── embeddings.py
│ ├── vector_store.py
│ ├── pdf_loader.py
│ ├── chunker.py
│
│ ├── prompts/
│ │ └── qa_expert.txt
│
│ └── agents/
│ └── qa_expert.py
│
├── data/
│ └── istqb_docs/ # ISTQB PDFs (gitignored)
│
├── chroma_db/ # vector database (gitignored)
│
├── tests/
│ ├── unit/
│ ├── integration/
│ └── golden/
│
├── pyproject.toml
├── .env.example
├── CLAUDE.md
└── README.md


---

# Quick Start

If **mimik AI Foundation** is already running locally:


git clone https://github.com/SaiVamsiKolla-QA/qa-agent.git

cd qa-agent
poetry install
cp .env.example .env


Then ingest documents and run the CLI.

---

# Setup

## 1 Install Dependencies


poetry install


---

## 2 Configure Environment Variables

Copy the example file:


cp .env.example .env


Example `.env` configuration:


MIMIK_ENDPOINT=http://localhost:8083/mimik-ai/openai/v1

MODEL_NAME=your-model-name
CHROMA_PATH=./chroma_db
TOP_K=4
CHUNK_SIZE=500
CHUNK_OVERLAP=100
EMBED_BATCH_SIZE=32


---

## 3 Start mimik AI Foundation

Ensure the mimik runtime is running locally.

Default endpoint expected by the system:


http://localhost:8083


---

# Ingest ISTQB Material

Place ISTQB PDFs inside:


data/istqb_docs/


Then run:


poetry run python -m qa_agent.ingest


This command will:

1. parse the PDF
2. split text into chunks
3. generate embeddings
4. populate the vector database

---

# Ask Questions

Run the CLI:


poetry run python -m qa_agent.cli


Example prompt:


What is equivalence partitioning?


---

# Example Response


Concept: Equivalence Partitioning

Definition
Equivalence partitioning is a black-box test design technique
where input data is divided into groups expected to behave similarly.

Real Example
A login form accepting passwords between 8 and 20 characters
creates partitions for valid length, too short, and too long inputs.

Suggested Test Cases

password length = 8 (valid)
password length = 7 (invalid)
password length = 21 (invalid)

Common Mistakes
Many testers repeatedly test values within the same partition
instead of selecting representative values.

Interview Explanation
Equivalence partitioning reduces the number of tests while
maintaining coverage by testing representative values.


---

# Testing Strategy

The project uses **three levels of testing**.

## Unit Tests

Each module contains dedicated tests.


pytest


---

## Integration Tests

Integration tests run against the **real mimik runtime**.


pytest -m integration


---

## Golden RAG Tests

A set of known ISTQB questions verifies:

1. concept correctness
2. correct ISTQB terminology
3. absence of hallucinated information

Phase 1 completes when **at least five golden questions pass all checks**.

---

# Why No AI Frameworks?

This project intentionally avoids frameworks such as:

- LangChain
- LlamaIndex
- CrewAI
- AutoGen
- LangGraph

These frameworks hide the internal mechanics of RAG systems.

The goal of this project is to **understand how AI systems work internally before using abstractions.**

---

# Roadmap

## Phase 1 (Current)

Single **QA Expert Agent**

Features:

- document ingestion
- chunking
- embeddings
- vector search
- CLI question answering

---

## Phase 2

**Test Case Generator Agent**

Capabilities:

- Boundary value analysis
- Equivalence partition testing
- Decision tables
- Pairwise testing

---

## Phase 3

**QA Interview Coach**

Features:

- generate interview questions
- evaluate candidate answers
- provide improvement suggestions

---

## Phase 4

FastAPI service with optional minimal web UI.

---

# Security

The repository does **not store sensitive data**.

The following are ignored by Git:

- ISTQB PDFs
- vector database files
- `.env` configuration

---

# Author

Senior QA Engineer transitioning toward:

**SDET → AI / ML Engineering**

Focus areas:

- AI agents
- QA automation
- RAG systems
- Python engineering

---

# License

MIT License