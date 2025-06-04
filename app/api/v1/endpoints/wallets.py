"""
/api/v1/wallets

POST   /                  - Создание нового кошелька
GET    /{wallet_uuid}     - Получение информации о кошельке
PATCH  /{wallet_uuid}     - Изменение статуса кошелька
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.logger import logger
from app.database import get_db
from app.models import Wallet, WalletStatus
from app.schemas import (
    WalletResponseSchema,
    WalletStatusSchema,
    WalletUpdateSchema
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post(
    "/",
    response_model=WalletResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create new wallet"
)
async def create_wallet(
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new wallet with initial balance 0 and ACTIVE status
    """
    new_wallet = Wallet()
    db.add(new_wallet)

    try:
        await db.commit()
        await db.refresh(new_wallet)
    except Exception as e:
        logger.error(f"Error creating wallet: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create wallet"
        )

    logger.info(f"Wallet created: {new_wallet.id}")
    return new_wallet


@router.get(
    "/{wallet_id}",
    response_model=WalletResponseSchema,
    summary="Get wallet info"
)
async def get_wallet(
    wallet_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get wallet information by ID
    """
    logger.debug(f"Fetching wallet: {wallet_id}")
    wallet = await db.get(Wallet, wallet_id)

    if not wallet:
        logger.warning(f"Wallet not found: {wallet_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    if wallet.status == WalletStatus.DELETED:
        logger.warning(f"Attempt to access deleted wallet: {wallet_id}")
        return {
            "id": wallet_id,
            "status": WalletStatusSchema.DELETED,
            "balance": wallet.balance,  # или обнулять
            "created_at": wallet.created_at,
            "updated_at": wallet.updated_at
        }

    logger.info(f"Wallet retrieved: {wallet_id}")
    return wallet


@router.patch(
    "/{wallet_id}",
    response_model=WalletResponseSchema,
    summary="Update wallet status"
)
async def update_wallet_status(
    wallet_id: UUID,
    update_data: WalletUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Update wallet status (ACTIVE/FROZEN/DELETED)
    """
    logger.info(
        f"Attempt to update wallet {wallet_id} status to {update_data.status}"
    )

    wallet = await db.get(Wallet, wallet_id)
    if not wallet:
        logger.warning(f"Wallet not found for update: {wallet_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    if wallet.status == WalletStatus.DELETED:
        logger.warning(f"Attempt to modify deleted wallet: {wallet_id}")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Cannot modify deleted wallet"
        )

    wallet.status = update_data.status  # type: ignore
    await db.commit()
    await db.refresh(wallet)

    logger.info(
        f"Wallet {wallet_id} status updated to {wallet.status}"
    )
    return wallet
