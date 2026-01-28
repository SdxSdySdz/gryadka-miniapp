"""Запуск только Telegram бота"""
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from bot.main import main
    import asyncio
    
    print("🤖 Запуск Telegram бота...")
    asyncio.run(main())
