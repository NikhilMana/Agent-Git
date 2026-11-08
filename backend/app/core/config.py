from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AgentGit"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./agentgit.db"
    AGENTGIT_MODE: str = "deterministic"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LOG_LEVEL: str = "INFO"
    POLICY_VERSION: str = "v1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

