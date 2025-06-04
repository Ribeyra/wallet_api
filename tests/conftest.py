import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.main import app
from app.database import Base, get_db


@pytest_asyncio.fixture
async def async_client():
    # Создаем engine и sessionmaker один раз
    test_engine = create_async_engine(settings.test_db_url)
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def get_fresh_db():
        async with async_session_factory() as session:
            yield session

    # Подменяем зависимость на фабрику сессий
    app.dependency_overrides[get_db] = get_fresh_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Создаем новый engine для тестов
    test_engine = create_async_engine(settings.test_db_url)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    # Удаляем таблицы после тестов
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:  # type: ignore
    test_engine = create_async_engine(settings.test_db_url)
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session  # type: ignore
