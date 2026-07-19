"""Judge model wrapper for DeepEval metrics.

One class covers every OpenAI-compatible endpoint — cloud OpenAI (default
base_url), Ollama, vLLM, or local mimik — so judge choice is pure config
(DECISIONS.md ADR-007). The API key is read from an environment variable
whose NAME is configured; the value is never stored in files.
"""

import json
import logging
import os
from typing import Any

from deepeval.models import DeepEvalBaseLLM
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAICompatibleJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by any OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> None:
        """Configure the judge.

        Args:
            model: Model name as the endpoint expects it.
            base_url: Endpoint base URL; None means cloud OpenAI.
            api_key_env: Name of the env var holding the API key.
            temperature: Sampling temperature; 0.0 for stable verdicts.
            timeout: Per-request timeout in seconds.
        """
        self.model = model
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.temperature = temperature
        self.timeout = timeout
        self._client: OpenAI | None = None

    def load_model(self) -> OpenAI:
        """Build (once) and return the underlying OpenAI-compatible client.

        Raises:
            RuntimeError: If the configured API key env var is unset while
                targeting cloud OpenAI (local endpoints accept any key).
        """
        if self._client is None:
            api_key = os.environ.get(self.api_key_env)
            if not api_key:
                if self.base_url is None:
                    raise RuntimeError(
                        f"judge requires env var {self.api_key_env} to be set "
                        "(cloud OpenAI endpoint)"
                    )
                api_key = "unused"
            self._client = OpenAI(
                base_url=self.base_url, api_key=api_key, timeout=self.timeout
            )
        return self._client

    def generate(self, prompt: str, schema: Any = None) -> Any:
        """Run one judge completion.

        Args:
            prompt: The metric's judge prompt.
            schema: Optional pydantic model class; when given, the reply is
                parsed and validated into an instance of it (DeepEval passes
                this for structured verdicts).

        Returns:
            The reply string, or a validated schema instance when schema
            is provided.
        """
        client = self.load_model()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        text = response.choices[0].message.content or ""
        logger.debug(f"judge_reply model={self.model} chars={len(text)}")
        if schema is None:
            return text
        return schema.model_validate_json(_extract_json(text))

    async def a_generate(self, prompt: str, schema: Any = None) -> Any:
        """Async interface required by DeepEval; delegates to generate()."""
        return self.generate(prompt, schema=schema)

    def get_model_name(self) -> str:
        """Return the judge model name for DeepEval reporting."""
        return self.model


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a possibly fenced reply.

    Args:
        text: Raw judge reply, possibly wrapped in markdown code fences
            or surrounded by prose.

    Returns:
        The JSON substring from the first '{' to the last '}'.

    Raises:
        ValueError: If no JSON object delimiters are found.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"judge reply contains no JSON object: {text[:200]!r}")
    candidate = text[start : end + 1]
    json.loads(candidate)
    return candidate


def build_judge(config: dict) -> OpenAICompatibleJudge:
    """Build a judge from the eval.yaml 'judge' mapping.

    Args:
        config: Mapping with keys model (required), base_url, api_key_env,
            temperature, timeout (all optional).

    Returns:
        A configured OpenAICompatibleJudge.
    """
    return OpenAICompatibleJudge(
        model=config["model"],
        base_url=config.get("base_url"),
        api_key_env=config.get("api_key_env", "OPENAI_API_KEY"),
        temperature=config.get("temperature", 0.0),
        timeout=config.get("timeout", 60),
    )
