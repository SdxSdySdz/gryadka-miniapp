"""API роуты для продуктов и категорий"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from database import get_session
from database.models import Product, Category, ProductImage, BadgeType
from shared.config import settings
from shared.utils import save_upload_file

router = APIRouter(prefix="/api/products", tags=["products"])


# ==================== СХЕМЫ ====================

class CategorySchema(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    sort_order: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ProductImageSchema(BaseModel):
    id: int
    image_url: str
    is_main: bool
    sort_order: int
    
    class Config:
        from_attributes = True


class ProductSchema(BaseModel):
    id: int
    category_id: int
    name: str
    description: Optional[str] = None
    price_kg: Optional[float] = None
    price_piece: Optional[float] = None
    price_package: Optional[float] = None
    price_box: Optional[float] = None
    price_multi: Optional[float] = None
    available_weights: Optional[List[int]] = None
    default_unit: str
    discount_percent: Optional[float] = None
    discount_fixed: Optional[float] = None
    old_price: Optional[float] = None
    badge: Optional[str] = None
    is_available: bool
    is_active: bool
    images: List[ProductImageSchema] = []
    
    class Config:
        from_attributes = True


class ProductCreateSchema(BaseModel):
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


# ==================== КАТЕГОРИИ ====================

@router.get("/categories", response_model=List[CategorySchema])
async def get_categories(
    include_inactive: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """Получить список категорий"""
    query = select(Category).order_by(Category.sort_order, Category.name)
    
    if not include_inactive:
        query = query.where(Category.is_active == True)
    
    result = await session.execute(query)
    categories = result.scalars().all()
    return categories


@router.get("/categories/{category_id}", response_model=CategorySchema)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить категорию по ID"""
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    return category


# ==================== ТОВАРЫ ====================

@router.get("/", response_model=List[ProductSchema])
async def get_products(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    badge: Optional[str] = None,
    is_available: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """Получить список товаров с фильтрами"""
    query = select(Product).options(selectinload(Product.images)).order_by(Product.sort_order, Product.name)
    
    # Фильтры
    conditions = []
    
    if not include_inactive:
        conditions.append(Product.is_active == True)
    
    if category_id:
        conditions.append(Product.category_id == category_id)
    
    if search:
        conditions.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    if badge:
        conditions.append(Product.badge == badge)
    
    if is_available is not None:
        conditions.append(Product.is_available == is_available)
    
    if min_price is not None:
        conditions.append(
            or_(
                Product.price_kg >= min_price,
                Product.price_piece >= min_price,
                Product.price_package >= min_price,
                Product.price_box >= min_price
            )
        )
    
    if max_price is not None:
        conditions.append(
            or_(
                Product.price_kg <= max_price,
                Product.price_piece <= max_price,
                Product.price_package <= max_price,
                Product.price_box <= max_price
            )
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить товар по ID"""
    result = await session.execute(
        select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return product


@router.get("/popular", response_model=List[ProductSchema])
async def get_popular_products(
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    """Получить популярные товары"""
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.is_active == True)
        .where(Product.is_available == True)
        .where(Product.badge == BadgeType.HIT.value)
        .order_by(Product.sort_order)
        .limit(limit)
    )
    products = result.scalars().all()
    return products


@router.get("/sale", response_model=List[ProductSchema])
async def get_sale_products(
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    """Получить товары по акции"""
    result = await session.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.is_active == True)
        .where(Product.is_available == True)
        .where(Product.badge == BadgeType.SALE.value)
        .order_by(Product.sort_order)
        .limit(limit)
    )
    products = result.scalars().all()
    return products
