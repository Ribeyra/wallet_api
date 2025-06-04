import enum
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class WalletStatus(enum.Enum):
    """Wallet status options."""
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DELETED = "DELETED"


class TransactionType(enum.Enum):
    """Transaction type options."""
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class TransactionStatus(enum.Enum):
    """Transaction status options."""
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Wallet(Base):
    """Wallet model to store user wallet information."""
    __tablename__ = "wallets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    balance = Column(BigInteger, default=0)
    status = Column(
        Enum(WalletStatus),
        default=WalletStatus.ACTIVE,
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Transaction(Base):
    """Transaction model to store all wallet operations."""
    __tablename__ = "transactions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id"),
        index=True
    )
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(BigInteger, nullable=False,)
    status = Column(Enum(TransactionStatus), nullable=False)
    # tx_hash = Column(String(66), unique=True)  # Хеш транзакции в блокчейне
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WalletAuditLog(Base):
    """Audit log for tracking wallet changes."""
    __tablename__ = "wallet_audit_log"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id"),
        index=True,
        nullable=False,
    )
    action = Column(String(100), nullable=False)  # Например: "BALANCE_UPDATE", "STATUS_CHANGE"  # noqa e501
    old_balance = Column(BigInteger)
    new_balance = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
