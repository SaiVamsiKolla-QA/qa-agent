"""Integration tests for the ingestion pipeline.

Runs load_pdf → chunk_texts → add_chunks end-to-end against a real
ChromaDB instance (tmp_path-backed) and real embeddings — no mocking.
"""
from pathlib import Path

import pytest

import qa_agent.vector_store as _vs
from qa_agent.chunker import chunk_texts
from qa_agent.config import settings
from qa_agent.pdf_loader import load_pdf
from qa_agent.vector_store import add_chunks, collection_count, query


def _make_text_pdf(path: Path, text: str) -> None:
    """Write a single-page PDF with extractable text to path.

    Uses the same raw-bytes approach as test_pdf_loader.py: object IDs
    1=Catalog, 2=Pages, 3=Page, 4=Content stream, 5=Font.
    """
    buf = bytearray()
    safe = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    stream = f"BT /F1 12 Tf 50 700 Td ({safe}) Tj ET".encode()

    xref_offsets: list[int] = []

    def emit(data: bytes) -> None:
        buf.extend(data)

    def start_obj(oid: int) -> None:
        xref_offsets.append(len(buf))
        emit(f"{oid} 0 obj\n".encode())

    def end_obj() -> None:
        emit(b"endobj\n")

    emit(b"%PDF-1.4\n")

    start_obj(1)
    emit(b"<< /Type /Catalog /Pages 2 0 R >>\n")
    end_obj()

    start_obj(2)
    emit(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n")
    end_obj()

    start_obj(3)
    emit(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
    )
    end_obj()

    start_obj(4)
    emit(f"<< /Length {len(stream)} >>\nstream\n".encode())
    emit(stream)
    emit(b"\nendstream\n")
    end_obj()

    start_obj(5)
    emit(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")
    end_obj()

    xref_pos = len(buf)
    emit(b"xref\n0 6\n")
    emit(b"0000000000 65535 f \n")
    for offset in xref_offsets:
        emit(f"{offset:010d} 00000 n \n".encode())
    emit(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n")
    emit(f"{xref_pos}\n".encode())
    emit(b"%%EOF\n")

    path.write_bytes(bytes(buf))


@pytest.fixture(autouse=True)
def _reset_store(tmp_path, monkeypatch):
    """Redirect ChromaDB to tmp_path and reset the cached client before each test."""
    monkeypatch.setattr(_vs.settings, "chroma_path", str(tmp_path))
    monkeypatch.setattr(_vs, "_client", None)
    yield
    monkeypatch.setattr(_vs, "_client", None)


@pytest.mark.integration
def test_ingest_pipeline_stores_chunks_in_vector_store(tmp_path: Path) -> None:
    """load_pdf → chunk_texts → add_chunks produces a non-empty collection."""
    # anchor (~18 words) + filler × 60 (~17 words × 60 = 1020) ≈ 1038 words total
    # chunk_size=500, overlap=100, stride=400 → 3 chunks
    anchor = (
        "Equivalence partitioning is a black-box test design technique "
        "that groups inputs into valid and invalid equivalence classes."
    )
    filler = (
        "Software testing finds defects in application behaviour "
        "and verifies that all specified requirements are met correctly. "
    )
    body = anchor + (filler * 60)

    pdf = tmp_path / "istqb_test.pdf"
    _make_text_pdf(pdf, body)

    pages = load_pdf(pdf)
    chunks = chunk_texts(
        pages, settings.chunk_size, settings.chunk_overlap,
        source_doc="istqb_test.pdf",
    )
    add_chunks(chunks)

    assert collection_count() > 0


@pytest.mark.integration
def test_ingest_pipeline_query_returns_chunk_containing_anchor_phrase(
    tmp_path: Path,
) -> None:
    """Query after ingestion returns a result whose text contains the queried phrase."""
    anchor_phrase = "black-box test design technique"
    anchor = (
        f"Equivalence partitioning is a {anchor_phrase} "
        "that groups inputs into valid and invalid equivalence classes."
    )
    filler = (
        "Software testing finds defects in application behaviour "
        "and verifies that all specified requirements are met correctly. "
    )
    body = anchor + (filler * 60)

    pdf = tmp_path / "istqb_test.pdf"
    _make_text_pdf(pdf, body)

    pages = load_pdf(pdf)
    chunks = chunk_texts(
        pages, settings.chunk_size, settings.chunk_overlap,
        source_doc="istqb_test.pdf",
    )
    add_chunks(chunks)

    results = query(anchor_phrase, top_k=settings.top_k)

    assert len(results) > 0
    assert any(anchor_phrase in r["text"] for r in results)
    assert results[0]["source_doc"] == "istqb_test.pdf"
    assert results[0]["page"] == 1
