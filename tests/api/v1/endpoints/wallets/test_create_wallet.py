import pytest
from httpx import AsyncClient

from app.models import Wallet, WalletStatus

pytestmark = pytest.mark.asyncio


class TestCreateWallet:
    async def test_create_wallet_success(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование успешного создания кошелька
        """
        # Отправляем запрос на создание кошелька
        response = await async_client.post("/api/v1/wallets/")

        # Проверяем статус код
        assert response.status_code == 201

        # Проверяем структуру ответа
        response_data = response.json()
        assert "id" in response_data
        assert "balance" in response_data
        assert response_data["balance"] == 0
        assert "status" in response_data
        assert response_data["status"] == "ACTIVE"

        # Проверяем, что кошелек действительно создан в БД
        wallet_id = response_data["id"]
        result = await db_session.get(Wallet, wallet_id)
        assert result is not None
        assert result.balance == 0
        assert result.status == WalletStatus.ACTIVE

    async def test_create_wallet_db_error(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """
        Тестирование обработки ошибки при создании кошелька
        """
        # Мокаем метод commit, чтобы вызвать ошибку
        async def mock_commit(*args, **kwargs):
            raise Exception("DB error")

        # Применяем мок
        monkeypatch.setattr(
            "sqlalchemy.ext.asyncio.AsyncSession.commit", mock_commit
        )

        # Отправляем запрос
        response = await async_client.post("/api/v1/wallets/")

        # Проверяем, что возвращается 500 ошибка
        assert response.status_code == 500
        assert response.json()["detail"] == "Could not create wallet"
