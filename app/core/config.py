# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, EmailStr


class Settings(BaseSettings):
    # App metadata
    app_name: str = "Birthday Buddy"

    # Database
    database_url: str

    # Cache
    redis_url: str

    # Authentication
    jwt_secret: str

    # Slack integration
    slack_api_token: str | None = None
    slack_webhook_url: AnyHttpUrl | None = None

    # Admin user seeding
    admin_email: EmailStr = "admin@example.com"
    admin_password: str = "adminpassword"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
