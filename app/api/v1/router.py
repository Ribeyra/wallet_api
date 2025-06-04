from fastapi import APIRouter
from app.api.v1.endpoints import wallets, operations


router = APIRouter(prefix="/api/v1")
router.include_router(wallets.router, tags=["wallets"])
router.include_router(operations.router, tags=["operations"])
