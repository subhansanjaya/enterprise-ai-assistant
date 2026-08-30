from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.include_router(chat_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
    }