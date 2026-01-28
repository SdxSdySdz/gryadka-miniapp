// Конфигурация API
const CONFIG = {
    // Для локальной разработки используйте http://localhost:8000
    // Для продакшена укажите URL вашего API на Render.com
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000'
        : 'https://gryadka-api.onrender.com', // Измените на ваш URL после деплоя на Render
    
    // Версия приложения
    VERSION: '1.0.0'
};

// Экспортируем для использования в других скриптах
window.CONFIG = CONFIG;
