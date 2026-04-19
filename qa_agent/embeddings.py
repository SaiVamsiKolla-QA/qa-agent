import logging
import time

from sentence_transformers import SentenceTransformer

from qa_agent.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        logger.debug(f"loading_embed_model model={settings.embed_model}")
        _model = SentenceTransformer(settings.embed_model)
    return _model


def embed_texts(texts: list[str], batch_size: int | None = None) -> list[list[float]]:
    """Generate embeddings for a list of texts in batches.

    Args:
        texts: List of strings to embed.
        batch_size: Override the config batch size if provided.

    Returns:
        List of embedding vectors (one per input text).
    """
    if not texts:
        return []

    effective_batch = batch_size or settings.embed_batch_size
    model = _get_model()

    start = time.monotonic()
    vectors = model.encode(
        texts,
        batch_size=effective_batch,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    duration = time.monotonic() - start

    logger.info(
        f"embeddings_created count={len(texts)} "
        f"batch_size={effective_batch} duration_s={duration:.2f}"
    )
    return [v.tolist() for v in vectors]
