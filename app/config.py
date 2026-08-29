from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"

    openai_api_key: str = ""

    pinecone_api_key: str = ""
    pinecone_index_name: str = "enterprise-ai-assistant"
    pinecone_namespace: str = "internal"

    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()