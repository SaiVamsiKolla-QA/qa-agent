"""Fixtures for the eval gate.

Mirrors the convention in tests/golden/conftest.py: live evaluation needs
mimik, so tests that call the real pipeline skip — not fail — when the
runtime is down. Schema-validation tests take no fixture and always run.
"""

import pytest


@pytest.fixture(scope="session")
def require_mimik() -> None:
    """Skip live eval tests if mimik AI Foundation is not reachable."""
    from qa_agent.llm_client import MimikUnavailableError, chat

    try:
        chat("Reply with pong only.", "ping")
    except MimikUnavailableError:
        pytest.skip(
            "mimik not reachable; live eval gate skipped — start with: mimoe start"
        )
