from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads all runtime configuration from .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    mimik_endpoint: str = "http://localhost:8083/mimik-ai/openai/v1"
    model_name: str = "mistral"
    mimik_api_key: str = "1234"
    chroma_path: str = "./chroma_db"
    chroma_collection: str = "istqb"
    top_k: int = 2
    abstain_threshold: float = 0.35
    chunk_size: int = 500
    chunk_overlap: int = 100
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_batch_size: int = 32
    hnsw_space: str = "cosine"
    llm_timeout: int = 30
    prompts_dir: Path = Path(__file__).parent / "prompts"


settings = Settings()
