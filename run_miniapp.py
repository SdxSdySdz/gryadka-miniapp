"""Запуск только Mini App"""
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    print("📱 Запуск Mini App...")
    print("🌐 URL: http://localhost:8001")
    
    uvicorn.run(
        "mini_app.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
