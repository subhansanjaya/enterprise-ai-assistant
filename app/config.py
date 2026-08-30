import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    # General application configuration.
    app_name: str = "Enterprise AI Assistant"
    environment: str = "development"
    log_level: str = "INFO"

    # OpenAI configuration.
    openai_api_key: str = ""

    # LangSmith observability and tracing.
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "enterprise-ai-assistant"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Pinecone vector store configuration.
    pinecone_api_key: str = ""
    pinecone_index_name: str = "enterprise-ai-assistant"
    pinecone_namespace: str = "internal"

    # Keycloak authentication and authorization.
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "enterprise-ai"
    keycloak_client_id: str = "backend-api"
    keycloak_ui_client_id: str = "enterprise-ai-ui"

    # MCP server used by agent tool calls.
    mcp_server_url: str = "http://127.0.0.1:8001/mcp"

    # PostgreSQL conversation persistence.
    database_url: str = (
        "postgresql+psycopg://keycloak:keycloak"
        "@localhost:5433/enterprise_ai"
    )

    # Model configuration.
    embedding_model: str = "text-embedding-3-small"

    # External-service timeout protection.
    llm_timeout_seconds: float = 30.0
    mcp_timeout_seconds: float = 15.0

    # Environment variables override these defaults. Local development
    # values can be supplied through .env, which must not be committed.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


# LangSmith's SDK reads tracing configuration from environment variables.
# Populate them from the validated application settings when tracing is enabled.
if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint