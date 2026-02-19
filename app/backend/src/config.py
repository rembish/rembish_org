from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    env: str = "production"
    debug: bool = False
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = "mysql+pymysql://app:devpassword@localhost:3306/rembish_org"

    # Session
    secret_key: str = "dev-secret-change-in-production"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Telegram
    telegram_token: str = ""
    telegram_chat_id: str = ""

    # Cloudflare Turnstile (CAPTCHA)
    turnstile_secret: str = ""  # Empty in dev = disabled

    # Instagram API
    instagram_account_id: str = ""
    instagram_page_token: str = ""

    # AeroDataBox (optional — empty = flight lookup disabled)
    aerodatabox_api_key: str = ""

    # GCS Storage (empty = use local storage for dev)
    gcs_bucket: str = ""

    # Vault encryption (base64-encoded 32-byte key)
    vault_encryption_key: str = ""


settings = Settings()
