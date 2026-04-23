import hashlib
import logging

logger = logging.getLogger(__name__)


def chunk_texts(
    pages: list[dict],
    chunk_size: int,
    chunk_overlap: int,
    source_doc: str,
) -> list[dict]:
    """Split page dicts into overlapping token-approximate chunks with provenance.

    Splits on whitespace; 'token' is approximated as one word.

    Args:
        pages: List of page dicts from load_pdf, each with 'page' and 'text'.
        chunk_size: Target chunk size in words.
        chunk_overlap: Number of words to overlap between consecutive chunks.
        source_doc: Filename or identifier of the source document.

    Returns:
        List of chunk dicts with keys: text, source_doc, page, chunk_index, chunk_id.

    Raises:
        ValueError: If chunk_overlap >= chunk_size.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap must be less than chunk_size: "
            f"chunk_size={chunk_size} chunk_overlap={chunk_overlap}"
        )

    words: list[str] = []
    word_pages: list[int] = []
    for page_dict in pages:
        page_words = page_dict["text"].split()
        words.extend(page_words)
        word_pages.extend([page_dict["page"]] * len(page_words))

    stride = chunk_size - chunk_overlap
    chunks: list[dict] = []
    chunk_index = 0
    start = 0

    while start < len(words):
        end = start + chunk_size
        text = " ".join(words[start:end])
        if text.strip():
            page = word_pages[start]
            chunk_id = hashlib.sha1(
                f"{source_doc}:{chunk_index}:{text[:100]}".encode()
            ).hexdigest()[:16]
            chunks.append({
                "text": text,
                "source_doc": source_doc,
                "page": page,
                "chunk_index": chunk_index,
                "chunk_id": chunk_id,
            })
            chunk_index += 1
        start += stride

    logger.debug(
        f"chunker_done total_words={len(words)} chunks={len(chunks)} "
        f"chunk_size={chunk_size} overlap={chunk_overlap}"
    )
    return chunks
