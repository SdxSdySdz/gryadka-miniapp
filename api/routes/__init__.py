"""Инициализация роутов API"""
from .products import router as products_router
from .cart import router as cart_router
from .orders import router as orders_router
from .admin import router as admin_router
from .common import router as common_router

__all__ = [
    'products_router',
    'cart_router',
    'orders_router',
    'admin_router',
    'common_router'
]
