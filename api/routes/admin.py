"""API роуты для админ-панели"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_
from pydantic import BaseModel

from database import get_session
from database.models import (
    Product, Category, ProductImage, User, Order, OrderStatus,
    PromoCode, DeliveryInterval, Settings as DBSettings, FAQ, Message
)
from shared.config import settings
from shared.utils import save_upload_file

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ==================== MIDDLEWARE ДЛЯ ПРОВЕРКИ АДМИНА ====================

async def verify_admin(telegram_id: int, session: AsyncSession):
    """Проверка прав администратора"""
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    return user


# ==================== СХЕМЫ ====================

class CategoryCreateSchema(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class ProductAdminSchema(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    price_kg: Optional[float] = None
    price_piece: Optional[float] = None
    price_package: Optional[float] = None
    price_box: Optional[float] = None
    price_multi: Optional[float] = None
    available_weights: Optional[List[int]] = None
    default_unit: str = "kg"
    discount_percent: Optional[float] = None
    discount_fixed: Optional[float] = None
    badge: Optional[str] = None
    is_available: bool = True
    is_active: bool = True
    sort_order: int = 0


class PromoCodeCreateSchema(BaseModel):
    code: str
    description: Optional[str] = None
    discount_percent: Optional[float] = None
    discount_fixed: Optional[float] = None
    min_order_amount: Optional[float] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True


class DeliveryIntervalCreateSchema(BaseModel):
    name: str
    time_from: str
    time_to: str
    available_from: str
    available_to: str
    is_active: bool = True
    sort_order: int = 0


class FAQCreateSchema(BaseModel):
    question: str
    answer: str
    sort_order: int = 0
    is_active: bool = True


class SettingsUpdateSchema(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


# ==================== КАТЕГОРИИ ====================

@router.post("/categories")
async def create_category(
    telegram_id: int,
    category_data: CategoryCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать категорию"""
    await verify_admin(telegram_id, session)
    
    category = Category(**category_data.dict())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    return {"message": "Категория создана", "id": category.id}


@router.put("/categories/{category_id}")
async def update_category(
    telegram_id: int,
    category_id: int,
    category_data: CategoryCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Обновить категорию"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    for key, value in category_data.dict(exclude_unset=True).items():
        setattr(category, key, value)
    
    await session.commit()
    
    return {"message": "Категория обновлена"}


@router.delete("/categories/{category_id}")
async def delete_category(
    telegram_id: int,
    category_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить категорию"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    await session.delete(category)
    await session.commit()
    
    return {"message": "Категория удалена"}


# ==================== ТОВАРЫ ====================

@router.post("/products")
async def create_product(
    telegram_id: int,
    product_data: ProductAdminSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать товар"""
    await verify_admin(telegram_id, session)
    
    product = Product(**product_data.dict())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    
    return {"message": "Товар создан", "id": product.id}


@router.put("/products/{product_id}")
async def update_product(
    telegram_id: int,
    product_id: int,
    product_data: ProductAdminSchema,
    session: AsyncSession = Depends(get_session)
):
    """Обновить товар"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    product.updated_at = datetime.utcnow()
    await session.commit()
    
    return {"message": "Товар обновлен"}


@router.delete("/products/{product_id}")
async def delete_product(
    telegram_id: int,
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить товар"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    await session.delete(product)
    await session.commit()
    
    return {"message": "Товар удален"}


@router.post("/products/bulk-update")
async def bulk_update_products(
    telegram_id: int,
    product_ids: List[int],
    action: str,  # delete, set_unavailable, set_available, set_inactive, set_active
    session: AsyncSession = Depends(get_session)
):
    """Массовое обновление товаров"""
    await verify_admin(telegram_id, session)
    
    if action == "delete":
        await session.execute(
            delete(Product).where(Product.id.in_(product_ids))
        )
    elif action == "set_unavailable":
        await session.execute(
            update(Product)
            .where(Product.id.in_(product_ids))
            .values(is_available=False)
        )
    elif action == "set_available":
        await session.execute(
            update(Product)
            .where(Product.id.in_(product_ids))
            .values(is_available=True)
        )
    elif action == "set_inactive":
        await session.execute(
            update(Product)
            .where(Product.id.in_(product_ids))
            .values(is_active=False)
        )
    elif action == "set_active":
        await session.execute(
            update(Product)
            .where(Product.id.in_(product_ids))
            .values(is_active=True)
        )
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")
    
    await session.commit()
    
    return {"message": f"Обновлено товаров: {len(product_ids)}"}


@router.post("/products/{product_id}/images")
async def upload_product_image(
    telegram_id: int,
    product_id: int,
    file: UploadFile = File(...),
    is_main: bool = Form(False),
    session: AsyncSession = Depends(get_session)
):
    """Загрузить изображение товара"""
    await verify_admin(telegram_id, session)
    
    # Проверяем товар
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Сохраняем файл
    file_content = await file.read()
    filename = save_upload_file(file_content, file.filename, settings.UPLOAD_DIR)
    
    # Если это главное изображение, снимаем флаг с остальных
    if is_main:
        await session.execute(
            update(ProductImage)
            .where(ProductImage.product_id == product_id)
            .values(is_main=False)
        )
    
    # Создаем запись об изображении
    product_image = ProductImage(
        product_id=product_id,
        image_url=f"/static/uploads/{filename}",
        is_main=is_main
    )
    session.add(product_image)
    await session.commit()
    
    return {"message": "Изображение загружено", "url": product_image.image_url}


# ==================== ЗАКАЗЫ ====================

@router.get("/orders")
async def get_all_orders(
    telegram_id: int,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """Получить все заказы"""
    await verify_admin(telegram_id, session)
    
    query = select(Order).order_by(Order.created_at.desc())
    
    if status:
        query = query.where(Order.status == status)
    
    if search:
        query = query.where(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Order.customer_name.ilike(f"%{search}%"),
                Order.customer_phone.ilike(f"%{search}%")
            )
        )
    
    query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    return orders


@router.put("/orders/{order_id}/status")
async def update_order_status(
    telegram_id: int,
    order_id: int,
    new_status: str,
    session: AsyncSession = Depends(get_session)
):
    """Обновить статус заказа"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    await session.commit()
    
    return {"message": "Статус заказа обновлен"}


# ==================== КЛИЕНТЫ ====================

@router.get("/users")
async def get_all_users(
    telegram_id: int,
    search: Optional[str] = None,
    is_blocked: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """Получить всех клиентов"""
    await verify_admin(telegram_id, session)
    
    query = select(User).where(User.is_admin == False).order_by(User.created_at.desc())
    
    if search:
        query = query.where(
            or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.phone.ilike(f"%{search}%")
            )
        )
    
    if is_blocked is not None:
        query = query.where(User.is_blocked == is_blocked)
    
    query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    users = result.scalars().all()
    
    return users


@router.put("/users/{user_id}/block")
async def block_user(
    telegram_id: int,
    user_id: int,
    block: bool,
    session: AsyncSession = Depends(get_session)
):
    """Заблокировать/разблокировать пользователя"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.is_blocked = block
    await session.commit()
    
    action = "заблокирован" if block else "разблокирован"
    return {"message": f"Пользователь {action}"}


# ==================== ПРОМОКОДЫ ====================

@router.post("/promo-codes")
async def create_promo_code(
    telegram_id: int,
    promo_data: PromoCodeCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать промокод"""
    await verify_admin(telegram_id, session)
    
    promo = PromoCode(**promo_data.dict())
    promo.code = promo.code.upper()
    session.add(promo)
    await session.commit()
    
    return {"message": "Промокод создан", "id": promo.id}


@router.get("/promo-codes")
async def get_promo_codes(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить все промокоды"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(PromoCode).order_by(PromoCode.created_at.desc())
    )
    promos = result.scalars().all()
    
    return promos


# ==================== ИНТЕРВАЛЫ ДОСТАВКИ ====================

@router.post("/delivery-intervals")
async def create_delivery_interval(
    telegram_id: int,
    interval_data: DeliveryIntervalCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать интервал доставки"""
    await verify_admin(telegram_id, session)
    
    interval = DeliveryInterval(**interval_data.dict())
    session.add(interval)
    await session.commit()
    
    return {"message": "Интервал доставки создан", "id": interval.id}


@router.get("/delivery-intervals")
async def get_delivery_intervals(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить все интервалы доставки"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(DeliveryInterval).order_by(DeliveryInterval.sort_order)
    )
    intervals = result.scalars().all()
    
    return intervals


@router.delete("/delivery-intervals/{interval_id}")
async def delete_delivery_interval(
    telegram_id: int,
    interval_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить интервал доставки"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(DeliveryInterval).where(DeliveryInterval.id == interval_id)
    )
    interval = result.scalar_one_or_none()
    
    if not interval:
        raise HTTPException(status_code=404, detail="Интервал не найден")
    
    await session.delete(interval)
    await session.commit()
    
    return {"message": "Интервал удален"}


# ==================== FAQ ====================

@router.post("/faq")
async def create_faq(
    telegram_id: int,
    faq_data: FAQCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Создать FAQ"""
    await verify_admin(telegram_id, session)
    
    faq = FAQ(**faq_data.dict())
    session.add(faq)
    await session.commit()
    
    return {"message": "FAQ создан", "id": faq.id}


@router.get("/faq")
async def get_all_faq(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить все FAQ"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(FAQ).order_by(FAQ.sort_order)
    )
    faqs = result.scalars().all()
    
    return faqs


# ==================== НАСТРОЙКИ ====================

@router.post("/settings")
async def update_setting(
    telegram_id: int,
    setting_data: SettingsUpdateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Обновить настройку"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(
        select(DBSettings).where(DBSettings.key == setting_data.key)
    )
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = setting_data.value
        if setting_data.description:
            setting.description = setting_data.description
    else:
        setting = DBSettings(**setting_data.dict())
        session.add(setting)
    
    await session.commit()
    
    return {"message": "Настройка обновлена"}


@router.get("/settings")
async def get_all_settings(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить все настройки"""
    await verify_admin(telegram_id, session)
    
    result = await session.execute(select(DBSettings))
    settings_list = result.scalars().all()
    
    return settings_list


# ==================== СТАТИСТИКА ====================

@router.get("/stats")
async def get_stats(
    telegram_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session)
):
    """Получить статистику"""
    await verify_admin(telegram_id, session)
    
    query = select(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total).label("total_revenue")
    ).where(Order.status != OrderStatus.CANCELLED.value)
    
    if date_from:
        query = query.where(Order.created_at >= date_from)
    if date_to:
        query = query.where(Order.created_at <= date_to)
    
    result = await session.execute(query)
    stats = result.one()
    
    return {
        "total_orders": stats.total_orders or 0,
        "total_revenue": float(stats.total_revenue or 0)
    }
