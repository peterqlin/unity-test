from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "My General Purpose API"
    DATABASE_URL: str | None = None
    SECRET_KEY: str | None = None

    # Google Cloud / Vertex AI
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str = "us-central1"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
