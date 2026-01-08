"""BoostHealth Service configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """BoostHealth Service settings."""

    # Service Configuration
    service_name: str = "boosthealth-service"
    port: int = 8001
    debug: bool = False
    
    # API Keys for authentication
    api_keys: str = ""  # Comma-separated list of valid API keys
    
    # CORS - comma-separated string in .env
    allowed_origins: str = "*"
    
    # LLM Configuration (for intent extraction)
    # Using XAI/Grok as the adapter implementation
    llm_provider: str = "grok"
    llm_api_key: str | None = None  # Alias for xai_api_key
    llm_model: str = "grok-4-fast-non-reasoning"
    llm_timeout_seconds: float = 30.0
    
    # XAI/Grok Configuration (backward compatibility)
    xai_api_key: str | None = None
    xai_model: str = "grok-4"
    xai_fast_model: str = "grok-4-fast-non-reasoning"
    xai_timeout_seconds: float = 180.0
    
    def model_post_init(self, __context):
        """Post-initialization to handle aliases."""
        # If llm_api_key not set but xai_api_key is, use xai_api_key
        if not self.llm_api_key and self.xai_api_key:
            object.__setattr__(self, 'llm_api_key', self.xai_api_key)
        # If xai_api_key not set but llm_api_key is, use llm_api_key
        elif not self.xai_api_key and self.llm_api_key:
            object.__setattr__(self, 'xai_api_key', self.llm_api_key)

    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str | None = None
    qdrant_apikey: str | None = None
    qdrant_collection_name: str = "fm_papers"
    qdrant_timeout_seconds: float = 600.0

    # Search Defaults
    default_limit: int = 5
    default_year_from: int = 2018
    default_min_citations: int = 5
    default_lexical_min: float = 0.05

    # Temperature Settings
    temperature_fast: float = 0.3
    temperature_main: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def valid_api_keys(self) -> set[str]:
        """Get set of valid API keys."""
        if not self.api_keys:
            return set()
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}
    
    @property
    def cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        if not self.allowed_origins:
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

