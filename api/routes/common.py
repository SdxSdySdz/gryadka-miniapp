"""API роуты для общих данных"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel

from database import get_session
from database.models import DeliveryInterval, Settings as DBSettings, FAQ
from shared.utils import is_time_in_interval

router = APIRouter(prefix="/api", tags=["common"])


# ==================== СХЕМЫ ====================

class DeliveryIntervalSchema(BaseModel):
    id: int
    name: str
    time_from: str
    time_to: str
    is_available_now: bool = False
    
    class Config:
        from_attributes = True


class SettingSchema(BaseModel):
    key: str
    value: str
    
    class Config:
        from_attributes = True


class FAQSchema(BaseModel):
    id: int
    question: str
    answer: str
    sort_order: int
    
    class Config:
        from_attributes = True


# ==================== ИНТЕРВАЛЫ ДОСТАВКИ ====================

@router.get("/delivery-intervals", response_model=List[DeliveryIntervalSchema])
async def get_available_intervals(session: AsyncSession = Depends(get_session)):
    """Получить доступные интервалы доставки"""
    result = await session.execute(
        select(DeliveryInterval)
        .where(DeliveryInterval.is_active == True)
        .order_by(DeliveryInterval.sort_order)
    )
    intervals = result.scalars().all()
    
    # Проверяем доступность каждого интервала
    now = datetime.utcnow()
    intervals_data = []
    
    for interval in intervals:
        is_available = is_time_in_interval(now, interval.available_from, interval.available_to)
        intervals_data.append({
            "id": interval.id,
            "name": interval.name,
            "time_from": interval.time_from,
            "time_to": interval.time_to,
            "is_available_now": is_available
        })
    
    return intervals_data


# ==================== НАСТРОЙКИ ====================

@router.get("/settings/public")
async def get_public_settings(session: AsyncSession = Depends(get_session)):
    """Получить публичные настройки"""
    public_keys = [
        "min_order_amount",
        "free_delivery_from",
        "delivery_cost",
        "contact_phone",
        "contact_address",
        "contact_hours",
        "contact_email"
    ]
    
    result = await session.execute(
        select(DBSettings).where(DBSettings.key.in_(public_keys))
    )
    settings = result.scalars().all()
    
    settings_dict = {s.key: s.value for s in settings}
    
    return settings_dict


# ==================== FAQ ====================

@router.get("/faq", response_model=List[FAQSchema])
async def get_faq(session: AsyncSession = Depends(get_session)):
    """Получить FAQ"""
    result = await session.execute(
        select(FAQ)
        .where(FAQ.is_active == True)
        .order_by(FAQ.sort_order)
    )
    faqs = result.scalars().all()
    
    return faqs


# ==================== СЕРВЕРНОЕ ВРЕМЯ ====================

@router.get("/server-time")
async def get_server_time():
    """Получить серверное время"""
    return {
        "time": datetime.utcnow().isoformat(),
        "timestamp": int(datetime.utcnow().timestamp())
    }
