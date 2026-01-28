"""Модели базы данных"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum

from .database import Base


class UnitType(PyEnum):
    """Единицы измерения"""
    KG = "kg"  # килограмм
    PIECE = "piece"  # штука
    PACKAGE = "package"  # упаковка
    BOX = "box"  # ящик


class BadgeType(PyEnum):
    """Типы бейджей для товаров"""
    HIT = "hit"  # Хит
    SALE = "sale"  # Акция
    RECOMMEND = "recommend"  # Советую


class OrderStatus(PyEnum):
    """Статусы заказа"""
    NEW = "new"  # Новый
    CONFIRMED = "confirmed"  # Подтвержден
    PREPARING = "preparing"  # Готовится
    READY = "ready"  # Готов
    DELIVERING = "delivering"  # Доставляется
    COMPLETED = "completed"  # Выполнен
    CANCELLED = "cancelled"  # Отменен


class PaymentType(PyEnum):
    """Типы оплаты"""
    CASH = "cash"  # Наличные
    CARD = "card"  # Карта
    ONLINE = "online"  # Онлайн


class DeliveryType(PyEnum):
    """Типы доставки"""
    DELIVERY = "delivery"  # Доставка
    PICKUP = "pickup"  # Самовывоз


# ==================== ПОЛЬЗОВАТЕЛИ ====================

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="user")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="user")


# ==================== КАТЕГОРИИ ====================

class Category(Base):
    """Модель категории"""
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


# ==================== ТОВАРЫ ====================

class Product(Base):
    """Модель товара"""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Цены по единицам измерения
    price_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_piece: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_package: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_box: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_multi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # За 2-3 штуки
    
    # Доступные граммовки (JSON array)
    available_weights: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # [100, 250, 500, 1000]
    
    # Единица измерения по умолчанию
    default_unit: Mapped[str] = mapped_column(String(20), default=UnitType.KG.value)
    
    # Скидки
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_fixed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    old_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Бейджи
    badge: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # hit, sale, recommend
    
    # Статус
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="product")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="product")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")


class ProductImage(Base):
    """Изображения товара"""
    __tablename__ = "product_images"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Отношения
    product: Mapped["Product"] = relationship("Product", back_populates="images")


# ==================== ИЗБРАННОЕ ====================

class Favorite(Base):
    """Избранные товары"""
    __tablename__ = "favorites"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    product: Mapped["Product"] = relationship("Product", back_populates="favorites")


# ==================== КОРЗИНА ====================

class CartItem(Base):
    """Элемент корзины"""
    __tablename__ = "cart_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # Может быть дробным для кг
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # kg, piece, package, box
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")


# ==================== ЗАКАЗЫ ====================

class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Контактные данные
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Доставка
    delivery_type: Mapped[str] = mapped_column(String(20), nullable=False)  # delivery, pickup
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_district: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_interval_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("delivery_intervals.id"), nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Оплата
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Суммы
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_cost: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Промокод
    promo_code_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("promo_codes.id"), nullable=True)
    
    # Комментарий
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Статус
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.NEW.value)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_interval: Mapped[Optional["DeliveryInterval"]] = relationship("DeliveryInterval")
    promo_code: Mapped[Optional["PromoCode"]] = relationship("PromoCode")


class OrderItem(Base):
    """Элемент заказа"""
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Отношения
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


# ==================== ПРОМОКОДЫ ====================

class PromoCode(Base):
    """Промокоды"""
    __tablename__ = "promo_codes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_fixed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    min_order_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================== ИНТЕРВАЛЫ ДОСТАВКИ ====================

class DeliveryInterval(Base):
    """Интервалы доставки"""
    __tablename__ = "delivery_intervals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    time_from: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    time_to: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    
    # Время, когда можно выбрать этот интервал
    available_from: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    available_to: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================== НАСТРОЙКИ ====================

class Settings(Base):
    """Настройки магазина"""
    __tablename__ = "settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== СООБЩЕНИЯ ====================

class Message(Base):
    """Сообщения от клиентов"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="messages")


# ==================== FAQ ====================

class FAQ(Base):
    """Часто задаваемые вопросы"""
    __tablename__ = "faq"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
