"""Скрипт для инициализации базы данных с тестовыми данными"""
import asyncio
from datetime import datetime, timedelta

from database import init_db, async_session_maker
from database.models import (
    Category, Product, ProductImage, User,
    Settings as DBSettings, FAQ, DeliveryInterval,
    PromoCode, BadgeType
)


async def create_initial_data():
    """Создание начальных данных"""
    print("🔄 Инициализация базы данных...")
    
    # Инициализируем таблицы
    await init_db()
    
    async with async_session_maker() as session:
        # Проверяем, есть ли уже данные
        from sqlalchemy import select
        result = await session.execute(select(Category))
        if result.first():
            print("⚠️  База данных уже содержит данные")
            return
        
        print("📦 Создание категорий...")
        categories = [
            Category(name="Все", description="Все товары", sort_order=0),
            Category(name="Ягоды", description="Свежие ягоды", sort_order=1),
            Category(name="Цитрусовые", description="Апельсины, лимоны, мандарины", sort_order=2),
            Category(name="Яблоки", description="Различные сорта яблок", sort_order=3),
            Category(name="Овощи", description="Свежие овощи", sort_order=4),
        ]
        
        for cat in categories:
            session.add(cat)
        
        await session.flush()
        
        print("🍎 Создание товаров...")
        products = [
            Product(
                category_id=categories[1].id,
                name="Клубника",
                description="Свежая сладкая клубника",
                price_kg=450.0,
                price_package=350.0,
                default_unit="kg",
                badge=BadgeType.HIT.value,
                is_available=True,
                is_active=True,
                sort_order=1
            ),
            Product(
                category_id=categories[2].id,
                name="Апельсины",
                description="Сочные апельсины",
                price_kg=120.0,
                price_piece=25.0,
                default_unit="kg",
                badge=BadgeType.SALE.value,
                old_price=150.0,
                is_available=True,
                is_active=True,
                sort_order=2
            ),
            Product(
                category_id=categories[3].id,
                name="Яблоки Гала",
                description="Сладкие красные яблоки",
                price_kg=85.0,
                price_piece=15.0,
                default_unit="kg",
                is_available=True,
                is_active=True,
                sort_order=3
            ),
            Product(
                category_id=categories[4].id,
                name="Помидоры",
                description="Спелые помидоры",
                price_kg=180.0,
                default_unit="kg",
                badge=BadgeType.RECOMMEND.value,
                is_available=True,
                is_active=True,
                sort_order=4
            ),
        ]
        
        for product in products:
            session.add(product)
        
        print("⚙️  Создание настроек...")
        settings = [
            DBSettings(key="min_order_amount", value="500", description="Минимальная сумма заказа"),
            DBSettings(key="free_delivery_from", value="2000", description="Бесплатная доставка от"),
            DBSettings(key="delivery_cost", value="200", description="Стоимость доставки"),
            DBSettings(key="contact_phone", value="+7 (900) 123-45-67", description="Телефон магазина"),
            DBSettings(key="contact_email", value="info@gryadka.ru", description="Email магазина"),
            DBSettings(key="contact_address", value="г. Москва, ул. Примерная, д. 1", description="Адрес магазина"),
            DBSettings(key="contact_hours", value="Пн-Вс: 9:00 - 21:00", description="Часы работы"),
            DBSettings(
                key="welcome_message",
                value="🍎 Добро пожаловать в Грядка!\n\nСвежие фрукты и овощи с доставкой!",
                description="Приветственное сообщение бота"
            ),
            DBSettings(
                key="about_text",
                value="Грядка - ваш надежный поставщик свежих фруктов и овощей. Мы работаем с лучшими поставщиками!",
                description="О магазине"
            ),
        ]
        
        for setting in settings:
            session.add(setting)
        
        print("🕐 Создание интервалов доставки...")
        intervals = [
            DeliveryInterval(
                name="Утренняя доставка",
                time_from="10:00",
                time_to="15:00",
                available_from="00:00",
                available_to="12:00",
                is_active=True,
                sort_order=1
            ),
            DeliveryInterval(
                name="Вечерняя доставка",
                time_from="15:00",
                time_to="22:00",
                available_from="07:00",
                available_to="12:00",
                is_active=True,
                sort_order=2
            ),
        ]
        
        for interval in intervals:
            session.add(interval)
        
        print("🎫 Создание промокода...")
        promo = PromoCode(
            code="WELCOME",
            description="Скидка 10% на первый заказ",
            discount_percent=10.0,
            min_order_amount=1000.0,
            max_uses=100,
            is_active=True,
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        session.add(promo)
        
        print("❓ Создание FAQ...")
        faqs = [
            FAQ(
                question="Как оформить заказ?",
                answer="Выберите товары, добавьте их в корзину и нажмите 'Оформить заказ'. Заполните данные доставки и подтвердите заказ.",
                sort_order=1,
                is_active=True
            ),
            FAQ(
                question="Какая минимальная сумма заказа?",
                answer="Минимальная сумма заказа составляет 500 рублей.",
                sort_order=2,
                is_active=True
            ),
            FAQ(
                question="Есть ли бесплатная доставка?",
                answer="Да, при заказе от 2000 рублей доставка бесплатная!",
                sort_order=3,
                is_active=True
            ),
        ]
        
        for faq in faqs:
            session.add(faq)
        
        await session.commit()
        
        print("✅ База данных успешно инициализирована!")
        print("\n📊 Создано:")
        print(f"   - Категорий: {len(categories)}")
        print(f"   - Товаров: {len(products)}")
        print(f"   - Настроек: {len(settings)}")
        print(f"   - Интервалов доставки: {len(intervals)}")
        print(f"   - Промокодов: 1")
        print(f"   - FAQ: {len(faqs)}")


if __name__ == "__main__":
    asyncio.run(create_initial_data())
