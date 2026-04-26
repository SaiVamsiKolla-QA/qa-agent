"""Unit tests for qa_agent.pdf_loader.load_pdf."""

from pathlib import Path

import pytest
from pypdf import PdfWriter

from qa_agent.pdf_loader import load_pdf

# ---------------------------------------------------------------------------
# Helpers — construct test PDFs entirely in memory, no committed fixtures
# ---------------------------------------------------------------------------


def _write_text_pdf(path: Path, pages_text: list[str]) -> None:
    """Write a minimal valid PDF with extractable text to *path*.

    Builds raw PDF bytes from scratch so no extra library is required beyond
    pypdf (already a project dependency).  Object ID layout for N pages:
      1 = Catalog, 2 = Pages, 3..N+2 = Page objects,
      N+3..2N+2 = Content streams, 2N+3 = Font.
    """
    buf = bytearray()
    xref_offsets: list[int] = []

    def emit(data: bytes) -> None:
        buf.extend(data)

    def start_obj(obj_id: int) -> None:
        xref_offsets.append(len(buf))
        emit(f"{obj_id} 0 obj\n".encode())

    def end_obj() -> None:
        emit(b"endobj\n")

    emit(b"%PDF-1.4\n")

    n = len(pages_text)
    page_ids = list(range(3, n + 3))
    content_ids = list(range(n + 3, 2 * n + 3))
    font_id = 2 * n + 3

    # Catalog
    start_obj(1)
    emit(b"<< /Type /Catalog /Pages 2 0 R >>\n")
    end_obj()

    # Pages root
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    start_obj(2)
    emit(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>\n".encode())
    end_obj()

    # Page objects
    for i, pid in enumerate(page_ids):
        start_obj(pid)
        emit(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_ids[i]} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n".encode()
        )
        end_obj()

    # Content streams — one per page
    for i, cid in enumerate(content_ids):
        safe = (
            pages_text[i].replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        )
        stream = f"BT /F1 12 Tf 50 700 Td ({safe}) Tj ET".encode()
        start_obj(cid)
        emit(f"<< /Length {len(stream)} >>\nstream\n".encode())
        emit(stream)
        emit(b"\nendstream\n")
        end_obj()

    # Font (standard Type 1 — Helvetica uses standard encoding, ASCII extracts cleanly)
    start_obj(font_id)
    emit(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")
    end_obj()

    # Cross-reference table (20 bytes per entry as required by PDF spec)
    xref_pos = len(buf)
    total_objs = font_id
    emit(b"xref\n")
    emit(f"0 {total_objs + 1}\n".encode())
    emit(b"0000000000 65535 f \n")  # free-list head
    for offset in xref_offsets:
        emit(f"{offset:010d} 00000 n \n".encode())

    emit(b"trailer\n")
    emit(f"<< /Size {total_objs + 1} /Root 1 0 R >>\n".encode())
    emit(b"startxref\n")
    emit(f"{xref_pos}\n".encode())
    emit(b"%%EOF\n")

    path.write_bytes(bytes(buf))


def _write_blank_pdf(path: Path, num_pages: int = 1) -> None:
    """Write a valid PDF whose pages have no extractable text to *path*."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as fh:
        writer.write(fh)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pdf_loader_returns_one_dict_per_page(tmp_path: Path) -> None:
    """load_pdf returns a list with exactly one dict per page."""
    pdf = tmp_path / "two_pages.pdf"
    _write_text_pdf(pdf, ["first page text", "second page text"])

    result = load_pdf(pdf)

    assert len(result) == 2


def test_pdf_loader_page_dicts_have_page_and_text_keys(tmp_path: Path) -> None:
    """Each returned dict has exactly the keys 'page' and 'text'."""
    pdf = tmp_path / "one_page.pdf"
    _write_text_pdf(pdf, ["some text"])

    result = load_pdf(pdf)

    assert len(result) == 1
    assert set(result[0].keys()) == {"page", "text"}


def test_pdf_loader_pages_are_1_indexed(tmp_path: Path) -> None:
    """Page numbers in returned dicts are 1-indexed."""
    pdf = tmp_path / "two_pages.pdf"
    _write_text_pdf(pdf, ["first", "second"])

    result = load_pdf(pdf)

    assert result[0]["page"] == 1
    assert result[1]["page"] == 2


def test_pdf_loader_text_content_appears_in_output(tmp_path: Path) -> None:
    """load_pdf includes the text embedded in the PDF in the returned dicts."""
    pdf = tmp_path / "content.pdf"
    _write_text_pdf(pdf, ["TESTMARKER"])

    result = load_pdf(pdf)

    assert len(result) == 1
    assert "TESTMARKER" in result[0]["text"]


def test_pdf_loader_multipage_text_preserved_per_page(tmp_path: Path) -> None:
    """Each page's text is kept separate and returned in document order."""
    pdf = tmp_path / "multipage.pdf"
    _write_text_pdf(pdf, ["PAGEONE", "PAGETWO", "PAGETHREE"])

    result = load_pdf(pdf)

    assert len(result) == 3
    assert "PAGEONE" in result[0]["text"]
    assert "PAGETWO" in result[1]["text"]
    assert "PAGETHREE" in result[2]["text"]


def test_pdf_loader_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """load_pdf raises FileNotFoundError when the path does not exist."""
    missing = tmp_path / "does_not_exist.pdf"

    with pytest.raises(FileNotFoundError):
        load_pdf(missing)


def test_pdf_loader_blank_pages_raise_value_error(tmp_path: Path) -> None:
    """load_pdf raises ValueError when the PDF contains no extractable text."""
    pdf = tmp_path / "blank.pdf"
    _write_blank_pdf(pdf, num_pages=2)

    with pytest.raises(ValueError):
        load_pdf(pdf)


def test_pdf_loader_corrupt_file_raises_exception(tmp_path: Path) -> None:
    """load_pdf raises an exception for a file that is not a valid PDF."""
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"this is not a valid pdf file at all")

    with pytest.raises(Exception):
        load_pdf(corrupt)
