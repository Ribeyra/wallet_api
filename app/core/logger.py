import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from pathlib import Path
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Настройка логгера с ротацией лог-файлов.
    """
    # Создаем директорию для логов, если её нет
    Path(settings.LOG_DIR).mkdir(exist_ok=True)

    # Форматтер
    formatter = logging.Formatter(settings.LOG_FORMAT)

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        filename=f"{settings.LOG_DIR}/{settings.LOG_FILE}",
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)

    # Настройка корневого логгера
    logger = logging.getLogger("wallet_api")
    logger.setLevel(settings.LOG_LEVEL)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Инициализация логгера при импорте модуля
logger = setup_logging()
