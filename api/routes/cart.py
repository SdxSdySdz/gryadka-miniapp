"""API роуты для корзины и избранного"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from database import get_session
from database.models import CartItem, Favorite, Product, User

router = APIRouter(prefix="/api", tags=["cart"])


# ==================== СХЕМЫ ====================

class CartItemSchema(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: float
    unit: str
    price_per_unit: float
    total: float
    product_image: str | None = None
    
    class Config:
        from_attributes = True


class CartItemCreateSchema(BaseModel):
    product_id: int
    quantity: float
    unit: str


class CartItemUpdateSchema(BaseModel):
    quantity: float


class FavoriteSchema(BaseModel):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True


# ==================== КОРЗИНА ====================

@router.get("/cart/{telegram_id}", response_model=List[CartItemSchema])
async def get_cart(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить корзину пользователя"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем товары в корзине
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id)
    )
    cart_items = result.scalars().all()
    
    # Формируем ответ
    items = []
    for item in cart_items:
        # Получаем информацию о товаре
        product_result = await session.execute(
            select(Product).where(Product.id == item.product_id)
        )
        product = product_result.scalar_one_or_none()
        
        if product:
            # Получаем главное изображение
            main_image = None
            if product.images:
                for img in product.images:
                    if img.is_main:
                        main_image = img.image_url
                        break
                if not main_image and product.images:
                    main_image = product.images[0].image_url
            
            items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "price_per_unit": item.price_per_unit,
                "total": item.quantity * item.price_per_unit,
                "product_image": main_image
            })
    
    return items


@router.post("/cart/{telegram_id}")
async def add_to_cart(
    telegram_id: int,
    item_data: CartItemCreateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Добавить товар в корзину"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем товар
    result = await session.execute(
        select(Product).where(Product.id == item_data.product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Определяем цену в зависимости от единицы измерения
    price_map = {
        "kg": product.price_kg,
        "piece": product.price_piece,
        "package": product.price_package,
        "box": product.price_box
    }
    
    price_per_unit = price_map.get(item_data.unit)
    
    if price_per_unit is None:
        raise HTTPException(status_code=400, detail="Недопустимая единица измерения")
    
    # Проверяем, есть ли уже такой товар в корзине
    result = await session.execute(
        select(CartItem).where(
            and_(
                CartItem.user_id == user.id,
                CartItem.product_id == item_data.product_id,
                CartItem.unit == item_data.unit
            )
        )
    )
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # Обновляем количество
        existing_item.quantity += item_data.quantity
    else:
        # Создаем новый элемент корзины
        cart_item = CartItem(
            user_id=user.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit=item_data.unit,
            price_per_unit=price_per_unit
        )
        session.add(cart_item)
    
    await session.commit()
    
    return {"message": "Товар добавлен в корзину"}


@router.put("/cart/{telegram_id}/{cart_item_id}")
async def update_cart_item(
    telegram_id: int,
    cart_item_id: int,
    update_data: CartItemUpdateSchema,
    session: AsyncSession = Depends(get_session)
):
    """Обновить количество товара в корзине"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем элемент корзины
    result = await session.execute(
        select(CartItem).where(
            and_(
                CartItem.id == cart_item_id,
                CartItem.user_id == user.id
            )
        )
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Элемент корзины не найден")
    
    if update_data.quantity <= 0:
        await session.delete(cart_item)
    else:
        cart_item.quantity = update_data.quantity
    
    await session.commit()
    
    return {"message": "Корзина обновлена"}


@router.delete("/cart/{telegram_id}/{cart_item_id}")
async def remove_from_cart(
    telegram_id: int,
    cart_item_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить товар из корзины"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем элемент корзины
    result = await session.execute(
        select(CartItem).where(
            and_(
                CartItem.id == cart_item_id,
                CartItem.user_id == user.id
            )
        )
    )
    cart_item = result.scalar_one_or_none()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Элемент корзины не найден")
    
    await session.delete(cart_item)
    await session.commit()
    
    return {"message": "Товар удален из корзины"}


@router.delete("/cart/{telegram_id}")
async def clear_cart(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Очистить корзину"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Удаляем все элементы корзины
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id)
    )
    cart_items = result.scalars().all()
    
    for item in cart_items:
        await session.delete(item)
    
    await session.commit()
    
    return {"message": "Корзина очищена"}


# ==================== ИЗБРАННОЕ ====================

@router.get("/favorites/{telegram_id}", response_model=List[int])
async def get_favorites(
    telegram_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить избранные товары пользователя"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем избранные товары
    result = await session.execute(
        select(Favorite.product_id).where(Favorite.user_id == user.id)
    )
    favorite_ids = result.scalars().all()
    
    return list(favorite_ids)


@router.post("/favorites/{telegram_id}/{product_id}")
async def add_to_favorites(
    telegram_id: int,
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Добавить товар в избранное"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, не добавлен ли уже товар в избранное
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user.id,
                Favorite.product_id == product_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {"message": "Товар уже в избранном"}
    
    # Добавляем в избранное
    favorite = Favorite(user_id=user.id, product_id=product_id)
    session.add(favorite)
    await session.commit()
    
    return {"message": "Товар добавлен в избранное"}


@router.delete("/favorites/{telegram_id}/{product_id}")
async def remove_from_favorites(
    telegram_id: int,
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить товар из избранного"""
    # Получаем пользователя
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Удаляем из избранного
    result = await session.execute(
        select(Favorite).where(
            and_(
                Favorite.user_id == user.id,
                Favorite.product_id == product_id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    if favorite:
        await session.delete(favorite)
        await session.commit()
    
    return {"message": "Товар удален из избранного"}
