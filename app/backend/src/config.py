from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    debug: bool = True
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "sqlite:///./dev.db"

    # Session
    secret_key: str = "dev-secret-change-in-production"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Telegram
    telegram_token: str = ""
    telegram_chat_id: str = ""


settings = Settings()
