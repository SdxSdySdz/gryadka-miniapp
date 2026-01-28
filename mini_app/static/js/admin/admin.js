// JavaScript для админ-панели

const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const user = tg.initDataUnsafe.user;
const userId = user ? user.id : null;

const API_BASE_URL = window.location.origin;

// Глобальное состояние
const adminState = {
    products: [],
    categories: [],
    orders: [],
    users: [],
    selectedItems: new Set(),
    currentPage: 1,
    pageSize: 20
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

// Проверка прав администратора
async function checkAdminAccess() {
    try {
        // Пробуем загрузить настройки (доступно только админу)
        await apiRequest(`/api/admin/settings?telegram_id=${userId}`);
        return true;
    } catch (error) {
        tg.showAlert('У вас нет прав администратора');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
        return false;
    }
}

// ==================== ТОВАРЫ ====================

async function loadProducts(filters = {}) {
    try {
        let endpoint = '/api/products/?include_inactive=true';
        
        if (filters.search) {
            endpoint += `&search=${encodeURIComponent(filters.search)}`;
        }
        if (filters.category_id) {
            endpoint += `&category_id=${filters.category_id}`;
        }
        if (filters.is_available !== undefined) {
            endpoint += `&is_available=${filters.is_available}`;
        }
        
        const products = await apiRequest(endpoint);
        adminState.products = products;
        renderProductsTable();
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

async function createProduct(data) {
    try {
        await apiRequest('/api/admin/products', {
            method: 'POST',
            body: JSON.stringify({
                ...data,
                telegram_id: userId
            })
        });
        
        tg.showPopup({
            title: 'Успешно',
            message: 'Товар создан',
            buttons: [{type: 'ok'}]
        });
        
        await loadProducts();
        closeModal('productModal');
    } catch (error) {
        console.error('Error creating product:', error);
    }
}

async function updateProduct(productId, data) {
    try {
        await apiRequest(`/api/admin/products/${productId}?telegram_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        tg.showPopup({
            title: 'Успешно',
            message: 'Товар обновлен',
            buttons: [{type: 'ok'}]
        });
        
        await loadProducts();
        closeModal('productModal');
    } catch (error) {
        console.error('Error updating product:', error);
    }
}

async function deleteProduct(productId) {
    tg.showConfirm('Удалить товар?', async (confirmed) => {
        if (confirmed) {
            try {
                await apiRequest(`/api/admin/products/${productId}?telegram_id=${userId}`, {
                    method: 'DELETE'
                });
                await loadProducts();
            } catch (error) {
                console.error('Error deleting product:', error);
            }
        }
    });
}

async function bulkUpdateProducts(action) {
    if (adminState.selectedItems.size === 0) {
        tg.showAlert('Выберите товары');
        return;
    }
    
    const productIds = Array.from(adminState.selectedItems);
    
    try {
        await apiRequest(`/api/admin/products/bulk-update?telegram_id=${userId}`, {
            method: 'POST',
            body: JSON.stringify({
                product_ids: productIds,
                action: action
            })
        });
        
        adminState.selectedItems.clear();
        await loadProducts();
    } catch (error) {
        console.error('Error bulk updating:', error);
    }
}

// ==================== КАТЕГОРИИ ====================

async function loadCategories() {
    try {
        const categories = await apiRequest('/api/products/categories?include_inactive=true');
        adminState.categories = categories;
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function createCategory(data) {
    try {
        await apiRequest('/api/admin/categories', {
            method: 'POST',
            body: JSON.stringify({
                ...data,
                telegram_id: userId
            })
        });
        
        tg.showPopup({
            title: 'Успешно',
            message: 'Категория создана',
            buttons: [{type: 'ok'}]
        });
        
        await loadCategories();
        closeModal('categoryModal');
    } catch (error) {
        console.error('Error creating category:', error);
    }
}

// ==================== ЗАКАЗЫ ====================

async function loadOrders(filters = {}) {
    try {
        let endpoint = `/api/admin/orders?telegram_id=${userId}`;
        
        if (filters.status) {
            endpoint += `&status=${filters.status}`;
        }
        if (filters.search) {
            endpoint += `&search=${encodeURIComponent(filters.search)}`;
        }
        
        const orders = await apiRequest(endpoint);
        adminState.orders = orders;
        renderOrdersTable();
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

async function updateOrderStatus(orderId, newStatus) {
    try {
        await apiRequest(`/api/admin/orders/${orderId}/status?telegram_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ new_status: newStatus })
        });
        
        await loadOrders();
    } catch (error) {
        console.error('Error updating order status:', error);
    }
}

// ==================== РЕНДЕРИНГ ====================

function renderProductsTable() {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;
    
    if (adminState.products.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state-admin">Нет товаров</td></tr>';
        return;
    }
    
    tbody.innerHTML = adminState.products.map(product => {
        const mainImage = product.images.find(img => img.is_main) || product.images[0];
        const imageUrl = mainImage ? mainImage.image_url : '/static/images/placeholder.jpg';
        
        return `
            <tr>
                <td><input type="checkbox" class="table-checkbox" onchange="toggleSelect(${product.id}, this.checked)"></td>
                <td><img src="${imageUrl}" alt="${product.name}" class="table-image"></td>
                <td><strong>${product.name}</strong></td>
                <td>${product.category_id}</td>
                <td>${product.price_kg || product.price_piece || 0} ₽</td>
                <td>
                    <span class="status-badge ${product.is_available ? 'status-available' : 'status-unavailable'}">
                        ${product.is_available ? 'В наличии' : 'Нет в наличии'}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${product.is_active ? 'status-active' : 'status-inactive'}">
                        ${product.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                </td>
                <td>
                    <div class="row-actions">
                        <button class="icon-button icon-edit" onclick="editProduct(${product.id})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="icon-button icon-delete" onclick="deleteProduct(${product.id})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function renderOrdersTable() {
    const tbody = document.getElementById('ordersTableBody');
    if (!tbody) return;
    
    if (adminState.orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state-admin">Нет заказов</td></tr>';
        return;
    }
    
    tbody.innerHTML = adminState.orders.map(order => `
        <tr>
            <td><strong>${order.order_number}</strong></td>
            <td>${order.customer_name}</td>
            <td>${order.customer_phone}</td>
            <td>${order.total.toFixed(2)} ₽</td>
            <td>
                <select onchange="updateOrderStatus(${order.id}, this.value)" class="form-select">
                    <option value="new" ${order.status === 'new' ? 'selected' : ''}>Новый</option>
                    <option value="confirmed" ${order.status === 'confirmed' ? 'selected' : ''}>Подтвержден</option>
                    <option value="preparing" ${order.status === 'preparing' ? 'selected' : ''}>Готовится</option>
                    <option value="ready" ${order.status === 'ready' ? 'selected' : ''}>Готов</option>
                    <option value="delivering" ${order.status === 'delivering' ? 'selected' : ''}>Доставляется</option>
                    <option value="completed" ${order.status === 'completed' ? 'selected' : ''}>Выполнен</option>
                    <option value="cancelled" ${order.status === 'cancelled' ? 'selected' : ''}>Отменен</option>
                </select>
            </td>
            <td>${new Date(order.created_at).toLocaleString('ru-RU')}</td>
            <td>
                <button class="icon-button icon-edit" onclick="viewOrder(${order.id})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                </button>
            </td>
        </tr>
    `).join('');
}

// ==================== МОДАЛЬНЫЕ ОКНА ====================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        // Сбрасываем форму
        const form = modal.querySelector('form');
        if (form) form.reset();
    }
}

// ==================== УТИЛИТЫ ====================

function toggleSelect(itemId, checked) {
    if (checked) {
        adminState.selectedItems.add(itemId);
    } else {
        adminState.selectedItems.delete(itemId);
    }
    
    updateBulkActionsVisibility();
}

function toggleSelectAll(checked) {
    adminState.selectedItems.clear();
    
    if (checked) {
        adminState.products.forEach(product => {
            adminState.selectedItems.add(product.id);
        });
    }
    
    const checkboxes = document.querySelectorAll('.table-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
    });
    
    updateBulkActionsVisibility();
}

function updateBulkActionsVisibility() {
    const bulkActions = document.getElementById('bulkActions');
    if (bulkActions) {
        bulkActions.style.display = adminState.selectedItems.size > 0 ? 'flex' : 'none';
    }
}

function searchItems(query) {
    // Реализуется в зависимости от текущей страницы
    if (window.location.pathname.includes('products')) {
        loadProducts({ search: query });
    } else if (window.location.pathname.includes('orders')) {
        loadOrders({ search: query });
    }
}

// Дебаунс для поиска
let searchTimeout;
function handleSearchInput(input) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        searchItems(input.value);
    }, 500);
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================

async function init() {
    // Проверяем права доступа
    const hasAccess = await checkAdminAccess();
    if (!hasAccess) return;
    
    // Загружаем данные в зависимости от страницы
    if (window.location.pathname.includes('products')) {
        await Promise.all([loadProducts(), loadCategories()]);
    } else if (window.location.pathname.includes('orders')) {
        await loadOrders();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
