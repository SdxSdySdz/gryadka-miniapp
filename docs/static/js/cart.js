// JavaScript для корзины и оформления заказа

const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const user = tg.initDataUnsafe.user;
const userId = user ? user.id : null;

const API_BASE_URL = window.CONFIG ? window.CONFIG.API_BASE_URL : window.location.origin;

let cartState = {
    items: [],
    settings: {},
    intervals: [],
    selectedPromo: null
};

// ==================== API ====================

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

// Загрузка корзины
async function loadCart() {
    if (!userId) {
        tg.showAlert('Необходимо авторизоваться');
        return;
    }
    
    try {
        const items = await apiRequest(`/api/cart/${userId}`);
        cartState.items = items;
        renderCart();
        updateSummary();
    } catch (error) {
        console.error('Error loading cart:', error);
    }
}

// Загрузка настроек
async function loadSettings() {
    try {
        const settings = await apiRequest('/api/settings/public');
        cartState.settings = settings;
        updateSummary();
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Загрузка интервалов доставки
async function loadIntervals() {
    try {
        const intervals = await apiRequest('/api/delivery-intervals');
        cartState.intervals = intervals;
        renderIntervals();
    } catch (error) {
        console.error('Error loading intervals:', error);
    }
}

// Обновление количества
async function updateQuantity(itemId, newQuantity) {
    if (newQuantity <= 0) {
        await removeItem(itemId);
        return;
    }
    
    try {
        await apiRequest(`/api/cart/${userId}/${itemId}`, {
            method: 'PUT',
            body: JSON.stringify({ quantity: newQuantity })
        });
        await loadCart();
    } catch (error) {
        console.error('Error updating quantity:', error);
    }
}

// Удаление товара
async function removeItem(itemId) {
    try {
        await apiRequest(`/api/cart/${userId}/${itemId}`, {
            method: 'DELETE'
        });
        await loadCart();
    } catch (error) {
        console.error('Error removing item:', error);
    }
}

// Очистка корзины
async function clearCart() {
    tg.showConfirm('Очистить корзину?', async (confirmed) => {
        if (confirmed) {
            try {
                await apiRequest(`/api/cart/${userId}`, {
                    method: 'DELETE'
                });
                await loadCart();
            } catch (error) {
                console.error('Error clearing cart:', error);
            }
        }
    });
}

// Применение промокода
async function applyPromoCode() {
    const input = document.getElementById('promoInput');
    const code = input.value.trim();
    
    if (!code) return;
    
    cartState.selectedPromo = code;
    updateSummary();
    tg.showPopup({
        title: 'Промокод',
        message: 'Промокод будет применен при оформлении заказа',
        buttons: [{type: 'ok'}]
    });
}

// Оформление заказа
async function checkout() {
    const form = document.getElementById('checkoutForm');
    const formData = new FormData(form);
    
    const orderData = {
        customer_name: formData.get('customer_name'),
        customer_phone: formData.get('customer_phone'),
        delivery_type: formData.get('delivery_type'),
        delivery_address: formData.get('delivery_address'),
        delivery_district: formData.get('delivery_district'),
        delivery_interval_id: parseInt(formData.get('delivery_interval_id')) || null,
        payment_type: formData.get('payment_type'),
        promo_code: cartState.selectedPromo,
        comment: formData.get('comment')
    };
    
    // Валидация
    if (!orderData.customer_name || !orderData.customer_phone) {
        tg.showAlert('Заполните все обязательные поля');
        return;
    }
    
    if (orderData.delivery_type === 'delivery' && !orderData.delivery_address) {
        tg.showAlert('Укажите адрес доставки');
        return;
    }
    
    try {
        const result = await apiRequest(`/api/orders/create/${userId}`, {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
        
        tg.showPopup({
            title: 'Заказ оформлен!',
            message: `Ваш заказ №${result.order_number} принят. Сумма: ${result.total.toFixed(2)} ₽`,
            buttons: [{type: 'ok'}]
        });
        
        setTimeout(() => {
            window.location.href = '/orders';
        }, 1500);
    } catch (error) {
        console.error('Error creating order:', error);
    }
}

// ==================== РЕНДЕРИНГ ====================

function renderCart() {
    const container = document.getElementById('cartItems');
    if (!container) return;
    
    if (cartState.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🛒</div>
                <div class="empty-state-text">Корзина пуста</div>
            </div>
        `;
        
        const checkoutBtn = document.getElementById('checkoutBtn');
        if (checkoutBtn) checkoutBtn.disabled = true;
        
        return;
    }
    
    container.innerHTML = cartState.items.map(item => `
        <div class="cart-item">
            <img src="${item.product_image || '/static/images/placeholder.jpg'}" alt="${item.product_name}" class="cart-item-image">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.product_name}</div>
                <div class="cart-item-price">${item.total.toFixed(2)} ₽</div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button class="quantity-button" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">−</button>
                        <span class="quantity-value">${item.quantity} ${getUnitShort(item.unit)}</span>
                        <button class="quantity-button" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    </div>
                    <button class="remove-item-button" onclick="removeItem(${item.id})">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function renderIntervals() {
    const select = document.getElementById('deliveryInterval');
    if (!select) return;
    
    select.innerHTML = '<option value="">Выберите интервал</option>' +
        cartState.intervals.map(interval => {
            const disabled = !interval.is_available_now;
            return `<option value="${interval.id}" ${disabled ? 'disabled' : ''}>
                ${interval.name} (${interval.time_from} - ${interval.time_to})
                ${disabled ? ' - недоступен' : ''}
            </option>`;
        }).join('');
}

function updateSummary() {
    const subtotal = cartState.items.reduce((sum, item) => sum + item.total, 0);
    const minOrder = parseFloat(cartState.settings.min_order_amount || 0);
    const freeDeliveryFrom = parseFloat(cartState.settings.free_delivery_from || 0);
    const deliveryCost = parseFloat(cartState.settings.delivery_cost || 0);
    
    // Проверяем тип доставки
    const deliveryType = document.querySelector('input[name="delivery_type"]:checked')?.value;
    const actualDeliveryCost = (deliveryType === 'delivery' && subtotal < freeDeliveryFrom) ? deliveryCost : 0;
    
    const total = subtotal + actualDeliveryCost;
    
    // Обновляем итоги
    const subtotalEl = document.getElementById('subtotal');
    const deliveryEl = document.getElementById('deliveryCost');
    const totalEl = document.getElementById('total');
    
    if (subtotalEl) subtotalEl.textContent = `${subtotal.toFixed(2)} ₽`;
    if (deliveryEl) {
        if (actualDeliveryCost > 0) {
            deliveryEl.textContent = `${actualDeliveryCost.toFixed(2)} ₽`;
        } else if (deliveryType === 'delivery') {
            deliveryEl.textContent = 'Бесплатно';
            deliveryEl.style.color = 'var(--primary-green)';
        } else {
            deliveryEl.textContent = '0 ₽';
        }
    }
    if (totalEl) totalEl.textContent = `${total.toFixed(2)} ₽`;
    
    // Проверяем минимальную сумму
    const minOrderWarning = document.getElementById('minOrderWarning');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    if (subtotal < minOrder) {
        if (minOrderWarning) {
            minOrderWarning.textContent = `Минимальная сумма заказа: ${minOrder} ₽. Добавьте еще товаров на ${(minOrder - subtotal).toFixed(2)} ₽`;
            minOrderWarning.style.display = 'flex';
        }
        if (checkoutBtn) checkoutBtn.disabled = true;
    } else {
        if (minOrderWarning) minOrderWarning.style.display = 'none';
        if (checkoutBtn) checkoutBtn.disabled = false;
        
        // Показываем информацию о бесплатной доставке
        if (deliveryType === 'delivery' && subtotal >= freeDeliveryFrom && freeDeliveryFrom > 0) {
            const freeDeliveryInfo = document.getElementById('freeDeliveryInfo');
            if (freeDeliveryInfo) {
                freeDeliveryInfo.textContent = `✓ Бесплатная доставка при заказе от ${freeDeliveryFrom} ₽`;
                freeDeliveryInfo.style.display = 'flex';
            }
        }
    }
}

function getUnitShort(unit) {
    const units = {
        'kg': 'кг',
        'piece': 'шт',
        'package': 'уп',
        'box': 'ящ'
    };
    return units[unit] || unit;
}

// Обработчики изменений формы
function onDeliveryTypeChange() {
    const deliveryType = document.querySelector('input[name="delivery_type"]:checked')?.value;
    const addressField = document.getElementById('addressField');
    const intervalField = document.getElementById('intervalField');
    
    if (deliveryType === 'delivery') {
        if (addressField) addressField.style.display = 'block';
        if (intervalField) intervalField.style.display = 'block';
    } else {
        if (addressField) addressField.style.display = 'none';
        if (intervalField) intervalField.style.display = 'none';
    }
    
    updateSummary();
}

// Навигация
function goBack() {
    window.history.back();
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

async function init() {
    await Promise.all([
        loadCart(),
        loadSettings(),
        loadIntervals()
    ]);
    
    // Устанавливаем обработчики
    const deliveryTypeInputs = document.querySelectorAll('input[name="delivery_type"]');
    deliveryTypeInputs.forEach(input => {
        input.addEventListener('change', onDeliveryTypeChange);
    });
    
    onDeliveryTypeChange();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
