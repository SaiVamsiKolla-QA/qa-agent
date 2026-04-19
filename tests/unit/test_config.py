from qa_agent.config import Settings


def test_settings_loads_without_env_file() -> None:
    """Settings() constructs without error when no .env file is present."""
    s = Settings(_env_file=None)
    assert s is not None


def test_settings_default_chunk_size() -> None:
    s = Settings(_env_file=None)
    assert s.chunk_size == 500


def test_settings_default_chunk_overlap() -> None:
    s = Settings(_env_file=None)
    assert s.chunk_overlap == 100


def test_settings_default_top_k() -> None:
    s = Settings(_env_file=None)
    assert s.top_k == 4


def test_settings_default_embed_batch_size() -> None:
    s = Settings(_env_file=None)
    assert s.embed_batch_size == 32
