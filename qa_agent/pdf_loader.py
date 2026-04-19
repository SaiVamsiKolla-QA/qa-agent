import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def load_pdf(path: Path) -> list[str]:
    """Extract text from each page of a PDF, one string per page.

    Args:
        path: Absolute or relative path to the PDF file.

    Returns:
        List of page text strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no text could be extracted from the PDF.
    """
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: path={path}")

    reader = PdfReader(str(path))
    pages: list[str] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        logger.debug(f"pdf_page_extracted page={i} chars={len(text)}")
        pages.append(text)

    total_chars = sum(len(p) for p in pages)
    if total_chars == 0:
        raise ValueError(f"PDF produced no text: path={path}")

    logger.debug(f"pdf_loaded pages={len(pages)} total_chars={total_chars}")
    return pages
