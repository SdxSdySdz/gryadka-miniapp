"""Инициализация модуля handlers"""
from .basic import router as basic_router
from .admin import router as admin_router

__all__ = ['basic_router', 'admin_router']
