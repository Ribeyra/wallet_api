"""
/api/v1/wallets/{wallet_uuid}/operations

POST   /                  - DEPOSIT/WITHDRAW операция
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select  # , update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models import (
    Wallet,
    Transaction,
    WalletAuditLog,
    WalletStatus,
    TransactionStatus
)
from app.schemas import WalletOperationSchema
from app.core.logger import logger

router = APIRouter(
    prefix="/wallets/{wallet_uuid}/operations",
    tags=["operations"]
)


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Perform DEPOSIT or WITHDRAW operation"
)
async def wallet_operation(
    wallet_uuid: UUID,
    operation: WalletOperationSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform DEPOSIT or WITHDRAW operation on wallet balance.
    """
    async with db.begin():
        # 1. Получаем и блокируем кошелек
        wallet = await db.execute(
            select(Wallet)
            .where(Wallet.id == wallet_uuid)
            .with_for_update()
        )
        wallet = wallet.scalar_one_or_none()

        # 2. Валидации (без side effects)
        if not wallet:
            logger.warning(f"Wallet not found: {wallet_uuid}")
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Wallet not found"
            )

        if wallet.status != WalletStatus.ACTIVE:
            logger.warning(
                f"Attempt to operate on non-active wallet {wallet_uuid}"
            )
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Can only operate on ACTIVE wallets"
            )

        if (
            operation.operation_type == "WITHDRAW" and
            wallet.balance < int(operation.amount)
        ):
            logger.warning(f"Insufficient funds in wallet {wallet_uuid}")
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Insufficient funds"
            )

        # 3. Вычисляем новый баланс
        new_balance = (
            wallet.balance + int(operation.amount)
            if operation.operation_type == "DEPOSIT"
            else wallet.balance - int(operation.amount)
        )

        # 4. Подготовка данных для сохранения
        transaction = Transaction(
            wallet_id=wallet_uuid,
            type=operation.operation_type,
            amount=int(operation.amount),
            status=TransactionStatus.SUCCESS,
        )

        audit_log = WalletAuditLog(
            wallet_id=wallet_uuid,
            action=f"BALANCE_{operation.operation_type.value}",
            old_balance=wallet.balance,
            new_balance=new_balance
        )

        wallet.balance = new_balance  # type: ignore

        # 5. Сохранение (единственный рискованный участок)
        try:
            db.add_all([transaction, audit_log])
            await db.commit()
        except Exception as e:
            logger.error(f"Database commit failed: {str(e)}")
            await db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Operation failed"
            )

    logger.info(
        f"Successful {operation.operation_type} of {operation.amount} "
        f"on wallet {wallet_uuid}. New balance: {new_balance}"
    )
    return {"new_balance": int(new_balance)}
