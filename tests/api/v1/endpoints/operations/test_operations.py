import asyncio
import pytest
import uuid
from http import HTTPStatus
from httpx import AsyncClient

from app.models import Wallet, WalletStatus

pytestmark = pytest.mark.asyncio


class TestWalletOperations:
    @pytest.mark.parametrize(
        "operation_type, initial_balance, amount, expected_balance",
        [
            ("DEPOSIT", 0, 100, 100),
            ("DEPOSIT", 50, 25, 75),
            ("WITHDRAW", 100, 40, 60),
            ("WITHDRAW", 100, 100, 0),
        ],
    )
    async def test_successful_operations(
        self,
        operation_type,
        initial_balance,
        amount,
        expected_balance,
        async_client: AsyncClient,
        db_session,
    ):
        """
        Тестирование успешных операций DEPOSIT и WITHDRAW
        """
        # 1. Создаем кошелек с начальным балансом
        wallet = Wallet(balance=initial_balance)
        db_session.add(wallet)
        await db_session.commit()

        # 2. Выполняем операцию
        await async_client.post(
            f"/api/v1/wallets/{wallet.id}/operations/",
            json={
                "operation_type": operation_type,
                "amount": amount,
            },
        )

        # 3. Проверяем ответ
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json()["balance"] == expected_balance

    async def test_insufficient_funds(
        self, async_client: AsyncClient, db_session
    ):
        """
        Тестирование попытки списания при недостаточном балансе
        """
        wallet = Wallet(balance=100)
        db_session.add(wallet)
        await db_session.commit()
        wallet_id = wallet.id

        response = await async_client.post(
            f"/api/v1/wallets/{wallet_id}/operations/",
            json={
                "operation_type": "WITHDRAW",
                "amount": 150,
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json()["detail"] == "Insufficient funds"

        # Проверяем, что баланс не изменился
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json()["balance"] == 100

    async def test_inactive_wallet(
        self, async_client: AsyncClient, db_session
    ):
        """
        Тестирование операций с неактивным кошельком
        """
        wallet = Wallet(status=WalletStatus.FROZEN)
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/wallets/{wallet.id}/operations/",
            json={
                "operation_type": "DEPOSIT",
                "amount": 100,
            },
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()["detail"] == "Can only operate on ACTIVE wallets"  # noqa e504

    async def test_nonexistent_wallet(self, async_client: AsyncClient):
        """
        Тестирование операций с несуществующим кошельком
        """
        random_uuid = uuid.uuid4()
        response = await async_client.post(
            f"/api/v1/wallets/{random_uuid}/operations/",
            json={
                "operation_type": "DEPOSIT",
                "amount": 100.0,
            },
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()["detail"] == "Wallet not found"

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"operation_type": "DEPOSIT", "amount": 0},
            {"operation_type": "DEPOSIT", "amount": -100},
            {"operation_type": "INVALID", "amount": 100},
            {"amount": 100},
            {"operation_type": "DEPOSIT"},
            {},
        ],
    )
    async def test_invalid_input(
        self, invalid_data, async_client: AsyncClient, db_session
    ):
        """
        Тестирование невалидных входных данных
        """
        wallet = Wallet()
        db_session.add(wallet)
        await db_session.commit()

        response = await async_client.post(
            f"/api/v1/wallets/{wallet.id}/operations/",
            json=invalid_data,
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_concurrent_deposits(
        self, async_client: AsyncClient, db_session
    ):
        """
        Тестирование конкурентных пополнений баланса
        """
        wallet = Wallet(balance=100)
        db_session.add(wallet)
        await db_session.commit()

        # Создаем несколько конкурентных запросов
        num_requests = 5
        amount = 10
        tasks = [
            async_client.post(
                f"/api/v1/wallets/{wallet.id}/operations/",
                json={
                    "operation_type": "DEPOSIT",
                    "amount": amount,
                },
            )
            for _ in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks)

        # Проверяем, что все запросы успешны
        for response in responses:
            assert response.status_code == HTTPStatus.OK

        # Проверяем итоговый баланс
        expected_balance = 100 + num_requests * amount

        # Проверяем через API
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json()["balance"] == expected_balance

    async def test_concurrent_withdrawals(
        self, async_client: AsyncClient, db_session
    ):
        """
        Тестирование конкурентных списаний с баланса
        """
        wallet = Wallet(balance=100)
        db_session.add(wallet)
        await db_session.commit()

        # Создаем несколько конкурентных запросов
        num_requests = 5
        amount = 10
        tasks = [
            async_client.post(
                f"/api/v1/wallets/{wallet.id}/operations/",
                json={
                    "operation_type": "WITHDRAW",
                    "amount": amount,
                },
            )
            for _ in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks)

        # Проверяем, что все запросы успешны
        for response in responses:
            assert response.status_code == HTTPStatus.OK

        # Проверяем итоговый баланс
        expected_balance = 100 - num_requests * amount
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json()["balance"] == expected_balance

    async def test_race_condition(self, async_client: AsyncClient, db_session):
        """
        Тестирование состояния гонки при недостаточном балансе
        """
        wallet = Wallet(balance=100)
        db_session.add(wallet)
        await db_session.commit()

        # Создаем несколько конкурентных запросов на списание
        num_requests = 3
        amount = 60  # Каждый запрос пытается списать 60, при балансе 100
        tasks = [
            async_client.post(
                f"/api/v1/wallets/{wallet.id}/operations/",
                json={
                    "operation_type": "WITHDRAW",
                    "amount": amount,
                },
            )
            for _ in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks)

        # Проверяем, что только один запрос успешен
        success_responses = [
            r for r in responses if r.status_code == HTTPStatus.OK
        ]
        assert len(success_responses) == 1

        # Проверяем, что остальные запросы получили ошибку
        failed_responses = [
            r for r in responses if r.status_code != HTTPStatus.OK
        ]
        assert len(failed_responses) == num_requests - 1
        for response in failed_responses:
            assert response.json()["detail"] == "Insufficient funds"

        # Проверяем итоговый баланс
        expected_balance = 100 - amount
        check_response = await async_client.get(f"/api/v1/wallets/{wallet.id}")
        assert check_response.json()["balance"] == expected_balance
