"""Главный файл FastAPI приложения"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from shared.config import settings
from api.routes import (
    products_router,
    cart_router,
    orders_router,
    admin_router,
    common_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске"""
    # Инициализация базы данных
    await init_db()
    yield


# Создание приложения
app = FastAPI(
    title="Грядка API",
    description="API для интернет-магазина фруктов и овощей",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# Для продакшена замените "*" на конкретные домены:
# allow_origins=["https://YOUR-USERNAME.github.io"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены (для разработки и GitHub Pages)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="mini_app/static"), name="static")

# Регистрация роутеров
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(common_router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Грядка API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
