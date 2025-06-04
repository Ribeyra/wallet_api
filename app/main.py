from fastapi import FastAPI
from app.api.v1 import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(api_router.router)


@app.get("/")
async def root():
    return {"message": "Wallet API"}
