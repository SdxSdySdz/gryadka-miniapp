"""Веб-приложение для Mini App"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Создание приложения
app = FastAPI(title="Грядка Mini App")

# Настройка путей
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Подключение статических файлов
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Шаблоны
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==================== РОУТЫ ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/cart", response_class=HTMLResponse)
async def cart(request: Request):
    """Страница корзины"""
    return templates.TemplateResponse("cart.html", {"request": request})


@app.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    """Страница заказов"""
    return templates.TemplateResponse("orders.html", {"request": request})


@app.get("/favorites", response_class=HTMLResponse)
async def favorites(request: Request):
    """Страница избранного"""
    return templates.TemplateResponse("favorites.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """Страница профиля"""
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int):
    """Страница товара"""
    return templates.TemplateResponse("product.html", {
        "request": request,
        "product_id": product_id
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Админ-панель"""
    return templates.TemplateResponse("admin/index.html", {"request": request})


@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products(request: Request):
    """Управление товарами"""
    return templates.TemplateResponse("admin/products.html", {"request": request})


@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(request: Request):
    """Управление заказами"""
    return templates.TemplateResponse("admin/orders.html", {"request": request})


@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request):
    """Настройки"""
    return templates.TemplateResponse("admin/settings.html", {"request": request})
