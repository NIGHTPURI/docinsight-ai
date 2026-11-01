from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PositiveInt


class Settings(BaseSettings):
    openai_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    upload_dir: str = "uploads"
    database_url: str = "sqlite:///./docinsight.db"
    max_upload_bytes: PositiveInt = 10 * 1024 * 1024
    max_pdf_pages: PositiveInt = 200
    max_document_chars: PositiveInt = 1_000_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
