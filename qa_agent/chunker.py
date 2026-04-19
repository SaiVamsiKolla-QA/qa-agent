import logging

logger = logging.getLogger(__name__)


def chunk_texts(
    pages: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Split a list of page strings into overlapping token-approximate chunks.

    Splits on whitespace; 'token' is approximated as one word.

    Args:
        pages: List of page text strings from the PDF loader.
        chunk_size: Target chunk size in words.
        chunk_overlap: Number of words to overlap between consecutive chunks.

    Returns:
        List of text chunk strings.

    Raises:
        ValueError: If chunk_overlap >= chunk_size.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap must be less than chunk_size: "
            f"chunk_size={chunk_size} chunk_overlap={chunk_overlap}"
        )

    words: list[str] = []
    for page in pages:
        words.extend(page.split())

    stride = chunk_size - chunk_overlap
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += stride

    logger.debug(
        f"chunker_done total_words={len(words)} chunks={len(chunks)} "
        f"chunk_size={chunk_size} overlap={chunk_overlap}"
    )
    return chunks
