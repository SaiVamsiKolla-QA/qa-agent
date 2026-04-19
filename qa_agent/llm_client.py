import logging
import time

from openai import APIConnectionError, APITimeoutError, OpenAI

from qa_agent.config import settings

logger = logging.getLogger(__name__)


class MimikUnavailableError(Exception):
    """Raised when the mimik AI Foundation runtime cannot be reached."""


def chat(system_prompt: str, user_message: str) -> str:
    """Send a chat completion request to the mimik LLM.

    Retries once with a 2-second backoff on timeout. Raises
    MimikUnavailableError if the endpoint is unreachable.

    Args:
        system_prompt: The system instruction string.
        user_message: The user turn content.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        MimikUnavailableError: If mimik is unreachable after retry.
        RuntimeError: If the LLM returns an empty response.
    """
    client = OpenAI(
        base_url=settings.mimik_endpoint,
        api_key=settings.mimik_api_key,
        timeout=settings.llm_timeout,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    tokens_in = len(system_prompt.split()) + len(user_message.split())
    logger.info(f"llm_called model={settings.model_name} tokens_in={tokens_in}")

    for attempt in range(2):
        try:
            start = time.monotonic()
            response = client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
            )
            duration = time.monotonic() - start
            logger.info(f"answer_returned duration_s={duration:.2f}")

            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("LLM returned an empty response")
            return content

        except APIConnectionError as exc:
            raise MimikUnavailableError(
                f"Cannot reach mimik at {settings.mimik_endpoint}"
            ) from exc

        except APITimeoutError:
            if attempt == 0:
                logger.debug("llm_timeout attempt=1 retrying after 2s")
                time.sleep(2)
                continue
            raise MimikUnavailableError(
                f"mimik timed out after {settings.llm_timeout}s"
            )

    raise MimikUnavailableError("LLM request failed after retry")
