import pytest
import uuid
from http import HTTPStatus
from httpx import AsyncClient

from app.models import Wallet, WalletStatus

pytestmark = pytest.mark.asyncio


class TestGetWallet:
    async def test_get_wallet_success(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование успешного получения информации о кошельке
        """
        # 1. Создаем тестовый кошелек напрямую в БД
        wallet = Wallet(balance=100, status=WalletStatus.ACTIVE)
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)

        # 2. Запрашиваем информацию о кошельке через API
        response = await async_client.get(f"/api/v1/wallets/{wallet.id}")

        # 3. Проверяем ответ
        assert response.status_code == HTTPStatus.OK

        response_data = response.json()
        assert response_data["id"] == str(wallet.id)
        assert response_data["balance"] == 100
        assert response_data["status"] == "ACTIVE"
        assert "created_at" in response_data
        assert response_data["updated_at"] is None

    async def test_get_nonexistent_wallet(self, async_client: AsyncClient):
        """
        Тестирование запроса несуществующего кошелька
        """
        # Используем случайный UUID
        random_uuid = uuid.uuid4()
        response = await async_client.get(f"/api/v1/wallets/{random_uuid}")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "Wallet not found"

    async def test_get_deleted_wallet(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование запроса удаленного кошелька
        """
        # 1. Создаем и "удаляем" кошелек
        wallet = Wallet(status=WalletStatus.DELETED)
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)

        # 2. Пытаемся получить информацию
        response = await async_client.get(f"/api/v1/wallets/{wallet.id}")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["status"] == WalletStatus.DELETED.value

    async def test_response_model_structure(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование соответствия ответа схеме WalletResponse
        """
        wallet = Wallet()
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/wallets/{wallet.id}")

        assert response.status_code == HTTPStatus.OK
        response_data = response.json()

        # Проверяем все обязательные поля схемы
        required_fields = {
            "id": str,
            "balance": int,
            "status": str,
            "created_at": str,
            "updated_at": type(None)  # Для нового кошелька updated_at должен быть None  # noqa e501
        }

        for field, field_type in required_fields.items():
            assert field in response_data
            assert isinstance(response_data[field], field_type)

    async def test_get_wallet_with_frozen_status(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование получения кошелька с статусом FROZEN
        """
        wallet = Wallet(status=WalletStatus.FROZEN)
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/wallets/{wallet.id}")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["status"] == "FROZEN"
