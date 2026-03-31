from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -------------------------------
    # App Config
    # -------------------------------
    app_name: str = "DataSpy Decision AI"
    app_env: str = "development"

    # -------------------------------
    # LLM Provider Selection
    # -------------------------------
    llm_provider: str = "groq"  # "openai" or "groq"

    # -------------------------------
    # OpenAI Config (fallback / premium)
    # -------------------------------
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # -------------------------------
    # Groq Config (fast + cheap)
    # -------------------------------
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # -------------------------------
    # Future RAG Config (placeholder)
    # -------------------------------
    embedding_provider: str = "huggingface"
    vector_store: str = "faiss"

    # -------------------------------
    # Environment file config
    # -------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()