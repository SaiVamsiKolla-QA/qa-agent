import logging
import time

from openai import APIConnectionError, APITimeoutError, OpenAI

from qa_agent.config import settings

logger = logging.getLogger(__name__)


class MimikUnavailableError(Exception):
    """Raised when the mimik AI Foundation runtime cannot be reached."""


def chat(
    system_prompt: str,
    user_message: str,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
    temperature: float | None = None,
    seed: int | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a chat completion request to the mimik LLM.

    Retries once with a 2-second backoff on timeout. Raises
    MimikUnavailableError if the endpoint is unreachable.

    Generation parameters resolve as argument -> settings -> unset. Any
    parameter that resolves to None is omitted from the request entirely,
    so the backend's own defaults apply (historical behavior).

    Args:
        system_prompt: The system instruction string.
        user_message: The user turn content.
        client: Injected OpenAI-compatible client; defaults to a client
            built from settings (mimik endpoint).
        model: Model name override; defaults to settings.model_name.
        temperature: Sampling temperature; defaults to settings.llm_temperature.
        seed: Sampling seed for reproducibility; defaults to settings.llm_seed.
        max_tokens: Reply-length cap; defaults to settings.llm_max_tokens.

    Returns:
        The assistant's reply as a plain string.

    Raises:
        MimikUnavailableError: If mimik is unreachable after retry.
        RuntimeError: If the LLM returns an empty response.
    """
    if client is None:
        client = OpenAI(
            base_url=settings.mimik_endpoint,
            api_key=settings.mimik_api_key,
            timeout=settings.llm_timeout,
        )
    model_name = model or settings.model_name
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    generation_params: dict = {}
    resolved = {
        "temperature": temperature
        if temperature is not None
        else settings.llm_temperature,
        "seed": seed if seed is not None else settings.llm_seed,
        "max_tokens": max_tokens if max_tokens is not None else settings.llm_max_tokens,
    }
    for name, value in resolved.items():
        if value is not None:
            generation_params[name] = value

    words_in = len(system_prompt.split()) + len(user_message.split())
    logger.info(f"llm_called model={model_name} words_in={words_in}")

    for attempt in range(2):
        try:
            start = time.monotonic()
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                **generation_params,
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
