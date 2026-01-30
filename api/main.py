"""Главный файл FastAPI приложения"""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from database import init_db
from shared.config import settings
from api.routes import (
    products_router,
    cart_router,
    orders_router,
    admin_router,
    common_router
)

# Путь к docs (Mini App)
DOCS_DIR = Path(__file__).parent.parent / "docs"


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


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "healthy"}


# === Mini App Routes ===

@app.get("/app/config.js")
async def get_config_js(request: Request):
    """Динамический config.js для Mini App"""
    # Используем тот же хост что и запрос
    host = request.headers.get("host", "localhost:8000")
    protocol = "https" if request.url.scheme == "https" else "http"
    base_url = f"{protocol}://{host}"
    
    config_content = f"""// Автогенерируемый конфиг
const CONFIG = {{
    API_BASE_URL: '{base_url}',
    VERSION: '1.0.0'
}};
window.CONFIG = CONFIG;
"""
    return HTMLResponse(content=config_content, media_type="application/javascript")


@app.get("/app", response_class=HTMLResponse)
@app.get("/app/", response_class=HTMLResponse)
async def get_miniapp_index():
    """Главная страница Mini App"""
    index_path = DOCS_DIR / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        # Заменяем путь к config.js
        content = content.replace('./config.js', '/app/config.js')
        content = content.replace('./static/', '/app/static/')
        return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>Mini App not found</h1>", status_code=404)


@app.get("/app/admin", response_class=HTMLResponse)
@app.get("/app/admin/", response_class=HTMLResponse)
async def get_admin_index():
    """Админ панель - главная"""
    index_path = DOCS_DIR / "admin" / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        content = content.replace('../config.js', '/app/config.js')
        content = content.replace('../static/', '/app/static/')
        content = content.replace('../index.html', '/app')
        content = content.replace('./products.html', '/app/admin/products')
        content = content.replace('./categories.html', '/app/admin/categories')
        content = content.replace('./orders.html', '/app/admin/orders')
        content = content.replace('./settings.html', '/app/admin/settings')
        return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>Admin not found</h1>", status_code=404)


@app.get("/app/admin/{page}", response_class=HTMLResponse)
async def get_admin_page(page: str):
    """Админ панель - страницы"""
    page_path = DOCS_DIR / "admin" / f"{page}.html"
    if page_path.exists():
        content = page_path.read_text(encoding="utf-8")
        content = content.replace('../config.js', '/app/config.js')
        content = content.replace('../static/', '/app/static/')
        content = content.replace('../index.html', '/app')
        content = content.replace('./index.html', '/app/admin/')
        content = content.replace('./products.html', '/app/admin/products')
        content = content.replace('./categories.html', '/app/admin/categories')
        content = content.replace('./orders.html', '/app/admin/orders')
        content = content.replace('./settings.html', '/app/admin/settings')
        return HTMLResponse(content=content)
    return HTMLResponse(content=f"<h1>Page {page} not found</h1>", status_code=404)


# Страницы Mini App (favorites, cart, profile, orders)
@app.get("/app/{page}", response_class=HTMLResponse)
async def get_app_page(page: str):
    """Страницы Mini App"""
    # Проверяем, не админка ли это
    if page == "admin":
        return await get_admin_index()

    page_path = DOCS_DIR / f"{page}.html"
    if page_path.exists():
        content = page_path.read_text(encoding="utf-8")
        content = content.replace('./config.js', '/app/config.js')
        content = content.replace('./static/', '/app/static/')
        # Замены для навигации
        content = content.replace("'/'", "'/app'")
        content = content.replace("'/" + "'", "'/app'")
        content = content.replace("href=\"/\"", "href=\"/app\"")
        return HTMLResponse(content=content)
    return HTMLResponse(content=f"<h1>Page {page} not found</h1>", status_code=404)


# Статические файлы Mini App
app.mount("/app/static", StaticFiles(directory=str(DOCS_DIR / "static")), name="app_static")


@app.get("/")
async def root():
    """Корневой эндпоинт - редирект на Mini App"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app")


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
