import logging
import os
from pydantic import ConfigDict, field_validator  # PostgresDsn,
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "WalletAPI"

    DATABASE_URL: str  # postgresql+asyncpg://user:password@db/wallet_db
    TEST_DATABASE_URL: str

    LOCAL_DATABASE_URL: str
    LOCAL_TEST_DATABASE_URL: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    LOG_DIR: str = "logs"
    LOG_FILE: str = "wallet_api.log"
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    LOG_BACKUP_COUNT: int = 5
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @field_validator("DATABASE_URL")
    def validate_db_url(cls, v):
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DB_URL должен начинаться с 'postgresql+asyncpg://'"
            )
        return v

    @property
    def db_url(self) -> str:
        """Автоматически выбирает правильный URL в зависимости от контекста"""
        return (
            self.DATABASE_URL
            if self.is_docker
            else self.LOCAL_DATABASE_URL
        )

    @property
    def test_db_url(self) -> str:
        return (
            self.TEST_DATABASE_URL
            if self.is_docker
            else self.LOCAL_TEST_DATABASE_URL
        )

    @property
    def is_docker(self) -> bool:
        """Определяет, работает ли приложение в контейнере"""
        return os.path.exists('/.dockerenv')

    model_config = ConfigDict(  # type: ignore
        env_file=".env",
        env_file_encoding="utf-8"
    )


# Создаём экземпляр настроек
settings = Settings()
