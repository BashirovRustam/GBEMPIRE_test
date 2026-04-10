from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.routers import webhook, orders

app = FastAPI(
    title="Dashboard API",
    description="API для интеграции RetailCRM и Supabase",
    version="1.0.0"
)

# CORS middleware
origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(webhook.router, prefix="/webhook", tags=["webhooks"])
app.include_router(orders.router, prefix="/api", tags=["api"])

# API endpoints (должны быть до статических файлов)
@app.get("/api/info")
async def api_info():
    return {
        "message": "Nova Dashboard API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Статические файлы (frontend) - монтируем в конце
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.FASTAPI_PORT,
        reload=settings.FASTAPI_ENV == "development"
    )
