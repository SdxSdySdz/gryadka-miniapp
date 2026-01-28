"""Вспомогательные функции"""
import hashlib
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


def generate_file_hash(file_content: bytes) -> str:
    """Генерация хеша файла"""
    return hashlib.md5(file_content).hexdigest()


def save_upload_file(file_content: bytes, filename: str, upload_dir: Path) -> str:
    """Сохранение загруженного файла"""
    # Создаем уникальное имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(filename).suffix
    new_filename = f"{timestamp}_{generate_file_hash(file_content)}{file_ext}"
    
    file_path = upload_dir / new_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return new_filename


def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:.2f} ₽"


def calculate_discount_price(price: float, discount_percent: Optional[float] = None, 
                             discount_fixed: Optional[float] = None) -> float:
    """Расчет цены со скидкой"""
    if discount_percent:
        return price * (1 - discount_percent / 100)
    elif discount_fixed:
        return max(0, price - discount_fixed)
    return price


def check_min_order_amount(cart_total: float, min_amount: float) -> bool:
    """Проверка минимальной суммы заказа"""
    return cart_total >= min_amount


def check_free_delivery(cart_total: float, free_delivery_from: float) -> bool:
    """Проверка бесплатной доставки"""
    return cart_total >= free_delivery_from


def is_time_in_interval(current_time: datetime, start_time: str, end_time: str) -> bool:
    """Проверка, находится ли время в интервале"""
    from datetime import time
    
    current = current_time.time()
    start = datetime.strptime(start_time, "%H:%M").time()
    end = datetime.strptime(end_time, "%H:%M").time()
    
    if start <= end:
        return start <= current <= end
    else:
        # Интервал через полночь
        return current >= start or current <= end
