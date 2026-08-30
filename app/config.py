import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"

    openai_api_key: str = ""

    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "enterprise-ai-assistant"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    pinecone_api_key: str = ""
    pinecone_index_name: str = "enterprise-ai-assistant"
    pinecone_namespace: str = "internal"

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "enterprise-ai"
    keycloak_client_id: str = "backend-api"

    mcp_server_url: str = "http://127.0.0.1:8001/mcp"

    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
