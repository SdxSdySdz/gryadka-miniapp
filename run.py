"""Скрипт для запуска всех компонентов"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    return subprocess.Popen(
        [sys.executable, "bot/main.py"],
        cwd=project_root,
        env=env
    )

def run_api():
    """Запуск API сервера"""
    print("🌐 Запуск API сервера...")
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_root,
        env=env
    )

def run_mini_app():
    """Запуск Mini App"""
    print("📱 Запуск Mini App...")
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mini_app.app:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=project_root,
        env=env
    )

def main():
    """Главная функция"""
    print("=" * 50)
    print("🍎 Запуск приложения Грядка")
    print("=" * 50)
    
    processes = []
    
    try:
        # Запускаем все компоненты
        processes.append(run_bot())
        processes.append(run_api())
        processes.append(run_mini_app())
        
        print("\n✅ Все компоненты запущены!")
        print("\n📝 Доступные эндпоинты:")
        print("   - API: http://localhost:8000")
        print("   - Mini App: http://localhost:8001")
        print("   - API Docs: http://localhost:8000/docs")
        print("\n⏸  Нажмите Ctrl+C для остановки\n")
        
        # Ждем завершения
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка приложения...")
        for process in processes:
            process.terminate()
        print("✅ Приложение остановлено")

if __name__ == "__main__":
    main()
