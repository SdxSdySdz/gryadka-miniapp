// Главный JavaScript файл для Mini App

// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Получаем данные пользователя
const user = tg.initDataUnsafe.user;
const userId = user ? user.id : null;

// API конфигурация
const API_BASE_URL = window.location.origin;

// Глобальное состояние
const state = {
    cart: [],
    favorites: [],
    categories: [],
    products: [],
    currentCategory: null,
    settings: {}
};

// ==================== API ФУНКЦИИ ====================

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка запроса');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        tg.showAlert(error.message || 'Произошла ошибка');
        throw error;
    }
}

// Загрузка категорий
async function loadCategories() {
    try {
        const categories = await apiRequest('/api/products/categories');
        state.categories = categories;
        renderCategories();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Загрузка товаров
async function loadProducts(categoryId = null, search = null) {
    try {
        let endpoint = '/api/products/';
        const params = new URLSearchParams();
        
        if (categoryId) {
            params.append('category_id', categoryId);
        }
        if (search) {
            params.append('search', search);
        }
        
        if (params.toString()) {
            endpoint += '?' + params.toString();
        }
        
        const products = await apiRequest(endpoint);
        state.products = products;
        renderProducts();
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

// Загрузка корзины
async function loadCart() {
    if (!userId) return;
    
    try {
        const cart = await apiRequest(`/api/cart/${userId}`);
        state.cart = cart;
        updateCartBadge();
    } catch (error) {
        console.error('Error loading cart:', error);
    }
}

// Загрузка избранного
async function loadFavorites() {
    if (!userId) return;
    
    try {
        const favorites = await apiRequest(`/api/favorites/${userId}`);
        state.favorites = favorites;
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

// Загрузка настроек
async function loadSettings() {
    try {
        const settings = await apiRequest('/api/settings/public');
        state.settings = settings;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Добавление в корзину
async function addToCart(productId, quantity = 1, unit = 'kg') {
    if (!userId) {
        tg.showAlert('Необходимо авторизоваться');
        return;
    }
    
    try {
        await apiRequest(`/api/cart/${userId}`, {
            method: 'POST',
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity,
                unit: unit
            })
        });
        
        await loadCart();
        tg.showPopup({
            title: 'Успешно',
            message: 'Товар добавлен в корзину',
            buttons: [{type: 'ok'}]
        });
    } catch (error) {
        console.error('Error adding to cart:', error);
    }
}

// Переключение избранного
async function toggleFavorite(productId) {
    if (!userId) {
        tg.showAlert('Необходимо авторизоваться');
        return;
    }
    
    try {
        const isFavorite = state.favorites.includes(productId);
        
        if (isFavorite) {
            await apiRequest(`/api/favorites/${userId}/${productId}`, {
                method: 'DELETE'
            });
        } else {
            await apiRequest(`/api/favorites/${userId}/${productId}`, {
                method: 'POST'
            });
        }
        
        await loadFavorites();
        renderProducts();
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

// ==================== РЕНДЕРИНГ ====================

function renderCategories() {
    const container = document.getElementById('categoriesContainer');
    if (!container) return;
    
    container.innerHTML = `
        <div class="category-item ${!state.currentCategory ? 'active' : ''}" onclick="selectCategory(null)">
            <div class="category-image-wrapper">
                <div class="category-image" style="background: var(--primary-green); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">Все</div>
            </div>
            <div class="category-name">Все</div>
        </div>
        ${state.categories.map(category => `
            <div class="category-item ${state.currentCategory === category.id ? 'active' : ''}" onclick="selectCategory(${category.id})">
                <div class="category-image-wrapper">
                    <img src="${category.image || '/static/images/placeholder.jpg'}" alt="${category.name}" class="category-image">
                </div>
                <div class="category-name">${category.name}</div>
            </div>
        `).join('')}
    `;
}

function renderProducts() {
    const container = document.getElementById('productsContainer');
    if (!container) return;
    
    if (state.products.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">Товары не найдены</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = state.products.map(product => {
        const isFavorite = state.favorites.includes(product.id);
        const mainImage = product.images.find(img => img.is_main) || product.images[0];
        const imageUrl = mainImage ? mainImage.image_url : '/static/images/placeholder.jpg';
        
        // Определяем цену
        let price = product.price_kg || product.price_piece || product.price_package || product.price_box;
        let unit = 'кг';
        
        if (product.default_unit === 'piece') {
            price = product.price_piece;
            unit = 'шт';
        } else if (product.default_unit === 'package') {
            price = product.price_package;
            unit = 'уп';
        } else if (product.default_unit === 'box') {
            price = product.price_box;
            unit = 'ящ';
        }
        
        return `
            <div class="product-card" onclick="openProduct(${product.id})">
                <div class="product-image-wrapper">
                    <img src="${imageUrl}" alt="${product.name}" class="product-image">
                    ${product.badge ? `<div class="product-badge badge-${product.badge}">${getBadgeText(product.badge)}</div>` : ''}
                    <button class="favorite-button ${isFavorite ? 'active' : ''}" onclick="event.stopPropagation(); toggleFavorite(${product.id})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                        </svg>
                    </button>
                </div>
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-price-row">
                        <span class="product-price">${price.toFixed(2)} ₽</span>
                        ${product.old_price ? `<span class="product-old-price">${product.old_price.toFixed(2)} ₽</span>` : ''}
                        <span class="product-unit">за ${unit}</span>
                    </div>
                    <button class="add-to-cart-button" onclick="event.stopPropagation(); addToCart(${product.id}, 1, '${product.default_unit}')">
                        В корзину
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getBadgeText(badge) {
    const badges = {
        'hit': 'Хит',
        'sale': 'Акция',
        'recommend': 'Советую'
    };
    return badges[badge] || badge;
}

function updateCartBadge() {
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    
    const itemCount = state.cart.reduce((sum, item) => sum + Math.ceil(item.quantity), 0);
    
    if (itemCount > 0) {
        badge.textContent = itemCount;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================

function selectCategory(categoryId) {
    state.currentCategory = categoryId;
    renderCategories();
    loadProducts(categoryId);
}

function openProduct(productId) {
    window.location.href = `/product/${productId}`;
}

function openCart() {
    window.location.href = '/cart';
}

function searchProducts() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    const query = searchInput.value.trim();
    loadProducts(state.currentCategory, query || null);
}

// Навигация
function navigateTo(page) {
    window.location.href = `/${page}`;
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

async function init() {
    // Показываем загрузку
    tg.MainButton.setText('Загрузка...');
    tg.MainButton.hide();
    
    // Загружаем данные
    await Promise.all([
        loadCategories(),
        loadProducts(),
        loadCart(),
        loadFavorites(),
        loadSettings()
    ]);
    
    // Настраиваем поиск
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(searchProducts, 500);
        });
    }
}

// Запуск при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
