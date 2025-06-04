import pytest
import uuid
from http import HTTPStatus
from httpx import AsyncClient

from app.models import Wallet, WalletStatus as WalletStatusDB
from app.schemas import WalletStatusSchema

pytestmark = pytest.mark.asyncio


class TestUpdateWalletStatus:
    @pytest.mark.parametrize(
        "new_status",
        [
            WalletStatusSchema.ACTIVE,
            WalletStatusSchema.FROZEN,
            WalletStatusSchema.DELETED,
        ],
    )
    async def test_update_wallet_status_success(
        self, new_status, async_client: AsyncClient, db_session
    ):
        """
        Тестирование успешного обновления статуса кошелька
        """
        # 1. Создаем тестовый кошелек
        wallet = Wallet(status=WalletStatusDB.ACTIVE)
        db_session.add(wallet)
        await db_session.commit()

        # 2. Отправляем запрос на обновление
        response = await async_client.patch(
            f"/api/v1/wallets/{wallet.id}",
            json={"status": new_status.value},
        )

        # 3. Проверяем ответ
        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert response_data["status"] == new_status.value
        assert response_data["id"] == str(wallet.id)
        assert response_data["updated_at"] is not None  # Должно обновиться

        # 4. Проверяем, что статус изменился в БД
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json().get("status") == new_status.value

    async def test_update_nonexistent_wallet(self, async_client: AsyncClient):
        """
        Тестирование обновления несуществующего кошелька
        """
        random_uuid = uuid.uuid4()
        response = await async_client.patch(
            f"/api/v1/wallets/{random_uuid}",
            json={"status": WalletStatusSchema.FROZEN.value},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "Wallet not found"

    async def test_update_deleted_wallet(
        self,
        async_client: AsyncClient,
        db_session
    ):
        """
        Тестирование попытки изменить удаленный кошелек
        """
        wallet = Wallet(status=WalletStatusDB.DELETED)
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.patch(
            f"/api/v1/wallets/{wallet.id}",
            json={"status": WalletStatusSchema.ACTIVE.value},
        )

        assert response.status_code == HTTPStatus.GONE
        assert response.json()["detail"] == "Cannot modify deleted wallet"

    @pytest.mark.parametrize(
        "invalid_status",
        [
            None,
            "",
            "INVALID_STATUS",
            123,
            {"invalid": "data"},
        ],
    )
    async def test_update_with_invalid_status(
        self, invalid_status, async_client: AsyncClient, db_session
    ):
        """
        Тестирование валидации входных данных
        """
        wallet = Wallet(status=WalletStatusDB.ACTIVE)
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.patch(
            f"/api/v1/wallets/{wallet.id}",
            json={"status": invalid_status},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_updated_at_changes_after_status_update(
        self, async_client: AsyncClient, db_session
    ):
        """
        Тестирование обновления поля updated_at при изменении статуса
        """
        # 1. Создаем кошелек
        wallet = Wallet(status=WalletStatusDB.ACTIVE)
        db_session.add(wallet)
        await db_session.commit()

        # 2. Получаем начальное состояние
        initial_response = await async_client.get(
            f"/api/v1/wallets/{wallet.id}"
        )
        initial_updated_at = initial_response.json()["updated_at"]
        assert initial_updated_at is None

        # 3. Меняем статус
        await async_client.patch(
            f"/api/v1/wallets/{wallet.id}",
            json={"status": WalletStatusSchema.FROZEN.value},
        )

        # 4. Проверяем, что updated_at изменился
        updated_response = await async_client.get(
            f"/api/v1/wallets/{wallet.id}"
        )
        assert updated_response.json()["updated_at"] is not None
