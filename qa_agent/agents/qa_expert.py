import logging

from qa_agent import llm_client, vector_store
from qa_agent.config import settings

logger = logging.getLogger(__name__)

ABSTAIN_MESSAGE = (
    "I don't have enough information from the available documents to answer this."
)
_PROMPT_WORD_WARN_THRESHOLD = 1500


def answer(question: str) -> str:
    """Answer an ISTQB question using retrieved context from the vector store.

    Retrieves the most relevant chunks from ChromaDB, checks whether the
    evidence is strong enough to warrant an LLM call, builds a numbered
    context block prompt, and returns the LLM's grounded response.

    Args:
        question: The user's question string.

    Returns:
        The LLM's answer as a plain string, or ABSTAIN_MESSAGE if
        retrieval evidence is too weak or empty.

    Raises:
        MimikUnavailableError: If mimik AI Foundation is unreachable.
        RuntimeError: If the LLM returns an empty response.
        FileNotFoundError: If qa_expert.txt is missing from prompts_dir.
    """
    logger.info(f"query_received length_chars={len(question)}")

    hits = vector_store.query(question, top_k=settings.top_k)

    for i, hit in enumerate(hits, start=1):
        logger.debug(
            f"retrieved_chunk rank={i} score={hit['score']} "
            f"source_doc={hit['source_doc']} page={hit['page']} "
            f"chunk_id={hit['chunk_id']}"
        )

    if not hits or hits[0]["score"] < settings.abstain_threshold:
        return ABSTAIN_MESSAGE

    system_prompt = (settings.prompts_dir / "qa_expert.txt").read_text()
    user_message = _build_user_message(hits, question)

    combined_words = len(system_prompt.split()) + len(user_message.split())
    if combined_words > _PROMPT_WORD_WARN_THRESHOLD:
        logger.warning(f"prompt_words={combined_words} exceeds_threshold=True")

    return llm_client.chat(system_prompt, user_message)


def _build_user_message(hits: list[dict], question: str) -> str:
    """Format retrieved chunks and question into a numbered context block string.

    Args:
        hits: List of hit dicts from vector_store.query, each with keys
            text, score, source_doc, page, chunk_index, chunk_id.
        question: The user's question string.

    Returns:
        Formatted string with numbered context blocks followed by the question.
    """
    blocks = []
    for i, hit in enumerate(hits, start=1):
        header = (
            f"[{i}] Source: {hit['source_doc']} | "
            f"Page {hit['page']} | chunk_id: {hit['chunk_id']}"
        )
        blocks.append(f"{header}\n{hit['text']}")

    context = "\n\n".join(blocks)
    return f"{context}\n\nQuestion: {question}"
