from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_async_engine(settings.db_url, echo=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

Base = declarative_base()


async def get_db():
    """Генератор сессий для FastAPI Depends"""
    async with SessionLocal() as session:
        yield session


async def close_db():
    """Закрыть соединения с БД при завершении приложения"""
    await engine.dispose()
