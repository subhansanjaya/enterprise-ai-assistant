from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"

    openai_api_key: str = ""

    pinecone_api_key: str = ""
    pinecone_index_name: str = "enterprise-ai-assistant"
    pinecone_namespace: str = "internal"
    
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "enterprise-ai"
    keycloak_client_id: str = "backend-api"

    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()