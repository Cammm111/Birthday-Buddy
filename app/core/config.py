# app/core/config.py

from datetime import date
from pydantic import AnyHttpUrl, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from passlib.context import CryptContext

# create your password‐hasher
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Settings(BaseSettings):
    # your existing env-backed fields
    jwt_secret: str               = Field(..., env="JWT_SECRET")
    slack_webhook_url: AnyHttpUrl = Field(..., env="SLACK_WEBHOOK_URL")

    admin_email: EmailStr    = Field(..., env="ADMIN_EMAIL")
    admin_password: str      = Field(..., env="ADMIN_PASSWORD")
    admin_dob: date          = Field(..., env="ADMIN_DOB")  # make sure ADMIN_DOB is in .env

    redis_url: str           = Field(..., env="REDIS_URL")
    database_url: str        = Field(..., env="DATABASE_URL")

    # pydantic-settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",    # or "forbid" if you want to catch typos
    )

    @property
    def hashed_admin_password(self) -> str:
        """
        bcrypt-hash the plain admin_password on demand.
        Used in init_db() to seed the superuser.
        """
        return pwd_ctx.hash(self.admin_password)


# instantiate once and import elsewhere
settings = Settings()
