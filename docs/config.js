// Конфигурация API
const CONFIG = {
    // Для локальной разработки используйте http://localhost:8000
    // Для продакшена укажите URL вашего API на VPS
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000'
        : 'http://46.149.66.138:8000', // Timeweb VPS
    
    // Версия приложения
    VERSION: '1.0.0'
};

// Экспортируем для использования в других скриптах
window.CONFIG = CONFIG;
