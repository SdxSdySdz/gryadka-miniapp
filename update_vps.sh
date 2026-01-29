#!/bin/bash
# Скрипт для обновления проекта на VPS

echo "🔄 Обновление проекта Грядка на VPS..."

# Обновить код
git pull

# Активировать venv
source venv/bin/activate

# Обновить базу данных - добавить поле icon
python -c "
from database.database import engine
from sqlalchemy import text
import asyncio

async def update_db():
    async with engine.begin() as conn:
        try:
            # Добавить поле icon
            await conn.execute(text('ALTER TABLE categories ADD COLUMN icon VARCHAR(10)'))
            print('✅ Поле icon добавлено в categories')
        except Exception as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                print('✅ Поле icon уже существует')
            else:
                print(f'❌ Ошибка: {e}')

asyncio.run(update_db())
"

# Перезапустить сервис
systemctl restart gryadka

# Проверить статус
sleep 2
systemctl status gryadka --no-pager -l

echo ""
echo "✅ Обновление завершено!"
