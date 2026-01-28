"""Обработчики для администратора"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func
from datetime import datetime, timedelta

from database.models import User, Order, OrderStatus
from database.database import async_session_maker
from bot.keyboards import get_back_keyboard

router = Router()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    """Статистика для администратора"""
    async with async_session_maker() as session:
        # Сегодняшние продажи
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.total))
            .where(Order.created_at >= today_start)
            .where(Order.status != OrderStatus.CANCELLED.value)
        )
        today_count, today_sum = today_result.one()
        
        # Вчерашние продажи
        yesterday_start = today_start - timedelta(days=1)
        yesterday_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.total))
            .where(Order.created_at >= yesterday_start)
            .where(Order.created_at < today_start)
            .where(Order.status != OrderStatus.CANCELLED.value)
        )
        yesterday_count, yesterday_sum = yesterday_result.one()
        
        # Месячные продажи
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.total))
            .where(Order.created_at >= month_start)
            .where(Order.status != OrderStatus.CANCELLED.value)
        )
        month_count, month_sum = month_result.one()
        
        # Всего пользователей
        users_result = await session.execute(select(func.count(User.id)))
        total_users = users_result.scalar()
        
        # Новые заказы
        new_orders_result = await session.execute(
            select(func.count(Order.id))
            .where(Order.status == OrderStatus.NEW.value)
        )
        new_orders = new_orders_result.scalar()
    
    text = (
        f"📊 <b>Статистика магазина</b>\n\n"
        f"<b>Сегодня:</b>\n"
        f"├ Заказов: {today_count or 0}\n"
        f"└ Выручка: {today_sum or 0:.2f} ₽\n\n"
        f"<b>Вчера:</b>\n"
        f"├ Заказов: {yesterday_count or 0}\n"
        f"└ Выручка: {yesterday_sum or 0:.2f} ₽\n\n"
        f"<b>Текущий месяц:</b>\n"
        f"├ Заказов: {month_count or 0}\n"
        f"└ Выручка: {month_sum or 0:.2f} ₽\n\n"
        f"<b>Общее:</b>\n"
        f"├ Клиентов: {total_users}\n"
        f"└ Новых заказов: {new_orders}\n"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_handler(callback: CallbackQuery):
    """Список клиентов"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User)
            .where(User.is_admin == False)
            .order_by(User.created_at.desc())
            .limit(20)
        )
        users = result.scalars().all()
    
    if users:
        text = "👥 <b>Последние клиенты</b> (макс. 20):\n\n"
        for user in users:
            name = user.first_name or user.username or f"ID{user.telegram_id}"
            status = "🚫" if user.is_blocked else "✅"
            text += f"{status} {name}\n"
            if user.phone:
                text += f"   📱 {user.phone}\n"
            text += f"   🆔 {user.telegram_id}\n\n"
    else:
        text = "👥 <b>Клиенты</b>\n\nПока нет зарегистрированных клиентов."
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders_handler(callback: CallbackQuery):
    """Список заказов"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        orders = result.scalars().all()
    
    if orders:
        text = "📦 <b>Последние заказы</b> (макс. 10):\n\n"
        
        status_emoji = {
            OrderStatus.NEW.value: "🆕",
            OrderStatus.CONFIRMED.value: "✅",
            OrderStatus.PREPARING.value: "👨‍🍳",
            OrderStatus.READY.value: "📦",
            OrderStatus.DELIVERING.value: "🚚",
            OrderStatus.COMPLETED.value: "✔️",
            OrderStatus.CANCELLED.value: "❌"
        }
        
        for order in orders:
            emoji = status_emoji.get(order.status, "📦")
            text += f"{emoji} <b>Заказ #{order.order_number}</b>\n"
            text += f"   💰 {order.total:.2f} ₽\n"
            text += f"   📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"   👤 {order.customer_name}\n\n"
    else:
        text = "📦 <b>Заказы</b>\n\nПока нет заказов."
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()
