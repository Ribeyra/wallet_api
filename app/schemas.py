from datetime import datetime
from enum import Enum
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    UUID4
)


class WalletStatusSchema(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    DELETED = "DELETED"


class WalletBase(BaseModel):
    status: WalletStatusSchema


class WalletResponseSchema(WalletBase):
    id: UUID4
    balance: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "balance": 0,
                "status": "ACTIVE",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": None
            }
        }
    )


class WalletUpdateSchema(WalletBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "FROZEN"
            }
        }
    )


class OperationTypeSchema(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationSchema(BaseModel):
    operation_type: OperationTypeSchema
    amount: int = Field(gt=0, description="Must be positive number")

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operation_type": "DEPOSIT",
                "amount": 100
            }
        }
    )
