"""Session-scoped fixture that skips the golden suite if mimik is not reachable."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_mimik_running() -> None:
    """Skip all golden tests if mimik AI Foundation is not reachable."""
    from qa_agent.llm_client import MimikUnavailableError, chat

    try:
        chat("Reply with pong only.", "ping")
    except MimikUnavailableError:
        pytest.skip(
            "mimik not reachable; skipping golden suite — start with: mimoe start"
        )
