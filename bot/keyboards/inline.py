"""Клавиатуры для Telegram бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from shared.config import settings


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛍 Открыть магазин",
                web_app=WebAppInfo(url=settings.MINI_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about"),
            InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
        ],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
        ]
    ])
    return keyboard


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню для администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚙️ Админ-панель",
                web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/admin")
            )
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_users"),
            InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")
        ]
    ])
    return keyboard


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard
