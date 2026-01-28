"""API роуты для заказов"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from database import get_session
from database.models import (
    Order, OrderItem, User, Product, CartItem, PromoCode,
    DeliveryInterval, Settings as DBSettings
)
from shared.utils import check_min_order_amount, check_free_delivery, is_time_in_interval

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ==================== СХЕМЫ ====================

class OrderItemSchema(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit: str
    price_per_unit: float
    subtotal: float


class OrderCreateSchema(BaseModel):
    customer_name: str
    customer_phone: str
    delivery_type: str  # delivery, pickup
    delivery_address: Optional[str] = None
    delivery_district: Optional[str] = None
    delivery_interval_id: Optional[int] = None
    delivery_date: Optional[datetime] = None
    payment_type: str
    promo_code: Optional[str] = None
    comment: Optional[str] = None


class OrderSchema(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_phone: str
    delivery_type: str
    delivery_address: Optional[str] = None
    delivery_district: Optional[str] = None
    delivery_date: Optional[datetime] = None
    payment_type: str
    subtotal: float
    delivery_cost: float
    discount_amount: float
    total: float
    status: str
    comment: Optional[str] = None
    created_at: datetime
    items: List[OrderItemSchema] = []
    
    class Config:
        from_attributes = True


# ==================== ЗАКАЗЫ ====================

@router.post("/create/{telegram_id}")
async def create_order(
    telegram_id: int,
    order_data: OrderCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать заказ из корзины"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем товары из корзины
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id)
    )
    cart_items = result.scalars().all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Корзина пуста")
    
    # Рассчитываем сумму
    subtotal = sum(item.quantity * item.price_per_unit for item in cart_items)
    
    # Получаем настройки
    min_order_result = await session.execute(
        select(DBSettings).where(DBSettings.key == "min_order_amount")
    )
    min_order_setting = min_order_result.scalar_one_or_none()
    min_order_amount = float(min_order_setting.value) if min_order_setting else 0
    
    # Проверяем минимальную сумму заказа
    if not check_min_order_amount(subtotal, min_order_amount):
        raise HTTPException(
            status_code=400,
            detail=f"Минимальная сумма заказа: {min_order_amount} ₽"
        )
    
    # Проверяем промокод
    discount_amount = 0
    promo_code_id = None
    
    if order_data.promo_code:
        result = await session.execute(
            select(PromoCode).where(
                and_(
                    PromoCode.code == order_data.promo_code.upper(),
                    PromoCode.is_active == True
                )
            )
        )
        promo = result.scalar_one_or_none()
        
        if promo:
            # Проверяем срок действия
            now = datetime.utcnow()
            if promo.valid_from and promo.valid_from > now:
                raise HTTPException(status_code=400, detail="Промокод еще не действует")
            if promo.valid_until and promo.valid_until < now:
                raise HTTPException(status_code=400, detail="Срок действия промокода истек")
            
            # Проверяем минимальную сумму
            if promo.min_order_amount and subtotal < promo.min_order_amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"Минимальная сумма для промокода: {promo.min_order_amount} ₽"
                )
            
            # Проверяем количество использований
            if promo.max_uses and promo.current_uses >= promo.max_uses:
                raise HTTPException(status_code=400, detail="Промокод исчерпан")
            
            # Рассчитываем скидку
            if promo.discount_percent:
                discount_amount = subtotal * (promo.discount_percent / 100)
            elif promo.discount_fixed:
                discount_amount = min(promo.discount_fixed, subtotal)
            
            promo_code_id = promo.id
            promo.current_uses += 1
    
    # Рассчитываем стоимость доставки
    delivery_cost = 0
    if order_data.delivery_type == "delivery":
        free_delivery_result = await session.execute(
            select(DBSettings).where(DBSettings.key == "free_delivery_from")
        )
        free_delivery_setting = free_delivery_result.scalar_one_or_none()
        free_delivery_from = float(free_delivery_setting.value) if free_delivery_setting else 0
        
        if not check_free_delivery(subtotal, free_delivery_from):
            delivery_cost_result = await session.execute(
                select(DBSettings).where(DBSettings.key == "delivery_cost")
            )
            delivery_cost_setting = delivery_cost_result.scalar_one_or_none()
            delivery_cost = float(delivery_cost_setting.value) if delivery_cost_setting else 0
    
    # Проверяем интервал доставки
    if order_data.delivery_interval_id:
        result = await session.execute(
            select(DeliveryInterval).where(DeliveryInterval.id == order_data.delivery_interval_id)
        )
        interval = result.scalar_one_or_none()
        
        if not interval or not interval.is_active:
            raise HTTPException(status_code=400, detail="Интервал доставки недоступен")
        
        # Проверяем, можно ли выбрать этот интервал сейчас
        now = datetime.utcnow()
        if not is_time_in_interval(now, interval.available_from, interval.available_to):
            raise HTTPException(
                status_code=400,
                detail=f"Этот интервал можно выбрать только с {interval.available_from} до {interval.available_to}"
            )
    
    # Итоговая сумма
    total = subtotal + delivery_cost - discount_amount
    
    # Генерируем номер заказа
    order_count_result = await session.execute(select(Order))
    order_count = len(order_count_result.scalars().all())
    order_number = f"ORD{datetime.utcnow().strftime('%Y%m%d')}{order_count + 1:04d}"
    
    # Создаем заказ
    order = Order(
        user_id=user.id,
        order_number=order_number,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        delivery_type=order_data.delivery_type,
        delivery_address=order_data.delivery_address,
        delivery_district=order_data.delivery_district,
        delivery_interval_id=order_data.delivery_interval_id,
        delivery_date=order_data.delivery_date,
        payment_type=order_data.payment_type,
        subtotal=subtotal,
        delivery_cost=delivery_cost,
        discount_amount=discount_amount,
        total=total,
        promo_code_id=promo_code_id,
        comment=order_data.comment
    )
    session.add(order)
    await session.flush()
    
    # Создаем элементы заказа
    for cart_item in cart_items:
        # Получаем название товара
        product_result = await session.execute(
            select(Product).where(Product.id == cart_item.product_id)
        )
        product = product_result.scalar_one_or_none()
        
        if product:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=product.name,
                quantity=cart_item.quantity,
                unit=cart_item.unit,
                price_per_unit=cart_item.price_per_unit,
                subtotal=cart_item.quantity * cart_item.price_per_unit
            )
            session.add(order_item)
            
            # Удаляем из корзины
            await session.delete(cart_item)
    
    await session.commit()
    
    return {
        "message": "Заказ успешно создан",
        "order_number": order_number,
        "order_id": order.id,
        "total": total
    }


@router.get("/{telegram_id}", response_model=List[OrderSchema])
async def get_user_orders(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить заказы пользователя"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем заказы
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    # Формируем ответ
    orders_data = []
    for order in orders:
        # Получаем элементы заказа
        items_result = await session.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = items_result.scalars().all()
        
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_type": order.delivery_type,
            "delivery_address": order.delivery_address,
            "delivery_district": order.delivery_district,
            "delivery_date": order.delivery_date,
            "payment_type": order.payment_type,
            "subtotal": order.subtotal,
            "delivery_cost": order.delivery_cost,
            "discount_amount": order.discount_amount,
            "total": order.total,
            "status": order.status,
            "comment": order.comment,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "price_per_unit": item.price_per_unit,
                    "subtotal": item.subtotal
                }
                for item in items
            ]
        }
        orders_data.append(order_dict)
    
    return orders_data


@router.get("/detail/{order_id}", response_model=OrderSchema)
async def get_order_detail(
    order_id: int,
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить детали заказа"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем заказ
    result = await session.execute(
        select(Order).where(
            and_(
                Order.id == order_id,
                Order.user_id == user.id
            )
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Получаем элементы заказа
    items_result = await session.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = items_result.scalars().all()
    
    order_dict = {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "delivery_type": order.delivery_type,
        "delivery_address": order.delivery_address,
        "delivery_district": order.delivery_district,
        "delivery_date": order.delivery_date,
        "payment_type": order.payment_type,
        "subtotal": order.subtotal,
        "delivery_cost": order.delivery_cost,
        "discount_amount": order.discount_amount,
        "total": order.total,
        "status": order.status,
        "comment": order.comment,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "price_per_unit": item.price_per_unit,
                "subtotal": item.subtotal
            }
            for item in items
        ]
    }
    
    return order_dict
