"""Базовые обработчики команд"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database.models import User, FAQ, Settings as DBSettings
from database.database import async_session_maker
from bot.keyboards import get_main_menu_keyboard, get_admin_menu_keyboard, get_back_keyboard
from shared.config import settings

router = Router()


async def get_or_create_user(telegram_id: int, username: str = None, 
                             first_name: str = None, last_name: str = None) -> User:
    """Получить или создать пользователя"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=(telegram_id == settings.ADMIN_ID)
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Получаем приветственное сообщение из настроек
    async with async_session_maker() as session:
        result = await session.execute(
            select(DBSettings).where(DBSettings.key == "welcome_message")
        )
        welcome_setting = result.scalar_one_or_none()
        
        if welcome_setting:
            welcome_text = welcome_setting.value
        else:
            welcome_text = (
                f"🍎 Добро пожаловать в <b>Грядка</b>!\n\n"
                f"Мы рады приветствовать вас в нашем магазине свежих фруктов и овощей! 🥕🍊\n\n"
                f"Здесь вы найдете:\n"
                f"✅ Свежие и качественные продукты\n"
                f"✅ Выгодные акции и скидки\n"
                f"✅ Быструю доставку\n"
                f"✅ Удобное оформление заказа\n\n"
                f"Нажмите кнопку ниже, чтобы начать покупки! 🛍"
            )
    
    # Выбираем клавиатуру в зависимости от роли
    if user.is_admin:
        keyboard = get_admin_menu_keyboard()
    else:
        keyboard = get_main_menu_keyboard()
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = await get_or_create_user(telegram_id=callback.from_user.id)
    
    if user.is_admin:
        keyboard = get_admin_menu_keyboard()
        text = "⚙️ <b>Админ-панель</b>\n\nВыберите действие:"
    else:
        keyboard = get_main_menu_keyboard()
        text = "🛍 <b>Главное меню</b>\n\nВыберите действие:"
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery):
    """Информация о магазине"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(DBSettings).where(DBSettings.key == "about_text")
        )
        about_setting = result.scalar_one_or_none()
        
        if about_setting:
            text = about_setting.value
        else:
            text = (
                "ℹ️ <b>О магазине Грядка</b>\n\n"
                "Мы - интернет-магазин свежих фруктов и овощей.\n\n"
                "🎯 Наша миссия: доставлять вам самые свежие и качественные продукты "
                "прямо к двери вашего дома.\n\n"
                "✨ Почему выбирают нас:\n"
                "• Только свежие продукты\n"
                "• Доставка в день заказа\n"
                "• Выгодные цены\n"
                "• Удобный интерфейс заказа\n"
                "• Акции и специальные предложения"
            )
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def contacts_handler(callback: CallbackQuery):
    """Контакты магазина"""
    async with async_session_maker() as session:
        # Получаем контактные данные из настроек
        keys = ["contact_phone", "contact_address", "contact_hours", "contact_email"]
        contacts = {}
        
        for key in keys:
            result = await session.execute(
                select(DBSettings).where(DBSettings.key == key)
            )
            setting = result.scalar_one_or_none()
            if setting:
                contacts[key] = setting.value
    
    text = "📞 <b>Контакты</b>\n\n"
    
    if contacts.get("contact_phone"):
        text += f"📱 Телефон: {contacts['contact_phone']}\n"
    if contacts.get("contact_email"):
        text += f"📧 Email: {contacts['contact_email']}\n"
    if contacts.get("contact_address"):
        text += f"📍 Адрес: {contacts['contact_address']}\n"
    if contacts.get("contact_hours"):
        text += f"🕐 Время работы: {contacts['contact_hours']}\n"
    
    text += f"\n💬 Telegram: @{(await callback.bot.get_me()).username}"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "faq")
async def faq_handler(callback: CallbackQuery):
    """Часто задаваемые вопросы"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(FAQ).where(FAQ.is_active == True).order_by(FAQ.sort_order)
        )
        faqs = result.scalars().all()
    
    if faqs:
        text = "❓ <b>Часто задаваемые вопросы</b>\n\n"
        for i, faq in enumerate(faqs, 1):
            text += f"<b>{i}. {faq.question}</b>\n"
            text += f"{faq.answer}\n\n"
    else:
        text = "❓ <b>Часто задаваемые вопросы</b>\n\nРаздел пока пуст."
    
    # Telegram имеет ограничение на длину сообщения
    if len(text) > 4000:
        text = text[:4000] + "..."
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()
