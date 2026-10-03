from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "GlobalTrade.ai API"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # PostgreSQL Connection String (using psycopg v3 synchronous driver)
    DATABASE_URL: str = "postgresql+psycopg://bhavikesh@localhost:5432/globaltrade_dev"

    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Auth0 Placeholders for Phase 1 (No auth enforcement in Phase 0)
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
