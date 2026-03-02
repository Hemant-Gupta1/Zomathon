const API_BASE = '/api/v1';

// Active State
let state = {
    userType: null, // 'user' or 'restaurant'
    userId: null,
    userData: null,
    activeRestId: null,
    cart: [],
    cartTotal: 0
};

// ---------------------------------------------------------
// Authentication & Initialization
// ---------------------------------------------------------
async function init() {
    // Check local storage for session
    const savedSession = localStorage.getItem('zomathon_session');
    if (savedSession) {
        state = JSON.parse(savedSession);
        document.getElementById('welcome-msg').textContent = `Hi, ${state.userData.Name || state.userData.RestName || state.userId}`;
        document.getElementById('user-display').classList.remove('hidden');
        
        if(state.userType === 'user') loadUserHome();
        else if (state.userType === 'restaurant') loadOwnerDashboard();
    } else {
        showView('view-login');
        document.getElementById('user-display').classList.add('hidden');
    }
}

async function login(username, type) {
    try {
        const endpoint = type === 'user' ? '/login/user' : '/login/restaurant';
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: username, password: 'password'})
        });
        
        const data = await res.json();
        if(data.status === 'success') {
            state.userType = type;
            state.userId = username;
            state.userData = data.data;
            
            localStorage.setItem('zomathon_session', JSON.stringify(state));
            init(); // Reinitialize with session
        }
    } catch(e) {
        console.error("Login failed", e);
    }
}

function logout() {
    localStorage.removeItem('zomathon_session');
    state = { userType: null, userId: null, userData: null, activeRestId: null, cart: [], cartTotal: 0 };
    document.getElementById('cart-items').innerHTML = '';
    document.getElementById('cart-subtotal').textContent = '₹0';
    init();
}

// ---------------------------------------------------------
// View Router
// ---------------------------------------------------------
function showView(viewId) {
    document.querySelectorAll('.view-container').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active-view');
    });
    const target = document.getElementById(viewId);
    if(target) {
        target.classList.remove('hidden');
        target.classList.add('active-view');
    }
}

// ---------------------------------------------------------
// User Homepage Logic
// ---------------------------------------------------------
async function loadUserHome() {
    showView('view-user-home');
    state.activeRestId = null; // Clear active restaurant
    state.cart = []; // Clear cart on home
    updateCartDisplay();
    
    try {
        const res = await fetch(`${API_BASE}/restaurants`);
        const data = await res.json();
        renderRestaurants(data);
    } catch(e) {
        console.error("Failed loading restaurants", e);
    }
    
    // Initial blank search to populate UI
    performSearch();
}

function renderRestaurants(restaurants) {
    const grid = document.getElementById('restaurants-grid');
    grid.innerHTML = '';
    
    restaurants.forEach(rest => {
        const el = document.createElement('div');
        el.className = 'rest-card';
        el.onclick = () => loadRestaurantMenu(rest.RestID, rest.Name, rest.Rating);
        el.innerHTML = `
            <div class="rest-image placeholder-img"><i class="fa-solid fa-store"></i></div>
            <div class="rest-info">
                <h4>${rest.Name}</h4>
                <div class="rest-meta">
                    <span class="rating"><i class="fa-solid fa-star"></i> ${rest.Rating}</span>
                    <span class="cuisine">${rest.Cuisine || 'Multi-Cuisine'}</span>
                </div>
            </div>
        `;
        grid.appendChild(el);
    });
}

function performSearch() {
    const q = document.getElementById('global-search').value;
    const isVeg = document.getElementById('veg-toggle').checked;
    const cat = document.getElementById('category-filter').value;
    
    fetchSearchResults(q, isVeg, cat);
}

// Debounce Search
let searchTimeout;
document.getElementById('global-search').addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(performSearch, 300);
});

async function fetchSearchResults(query, isVeg, category) {
    if(!query && !isVeg && category === "All") {
        document.getElementById('search-results-section').classList.add('hidden');
        return;
    }
    
    document.getElementById('search-results-section').classList.remove('hidden');
    
    try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&veg_only=${isVeg}&category=${category}`);
        const data = await res.json();
        renderSearchResults(data);
    } catch(e) {
        console.error("Search failed", e);
    }
}

function renderSearchResults(items) {
    const grid = document.getElementById('search-grid');
    grid.innerHTML = '';
    
    if(items.length === 0) {
        grid.innerHTML = '<p class="text-muted">No dishes found matching your criteria.</p>';
        return;
    }
    
    items.forEach(item => {
        const typeIcon = item.Is_Veg ? '<i class="fa-solid fa-leaf" style="color: #22c55e;"></i>' : '<i class="fa-solid fa-drumstick-bite" style="color: #ef4444;"></i>';
        const el = document.createElement('div');
        el.className = 'item-card search-card';
        el.innerHTML = `
            <div class="item-header">
                <span class="item-type">${typeIcon}</span>
                <span class="item-category">${item.Category} • ${item.Size}</span>
            </div>
            <h4 class="item-name">${item.Name}</h4>
            <div class="search-rest-meta">
                <small>From <strong style="color:var(--primary)">${item.RestName}</strong></small>
                <small class="rating"><i class="fa-solid fa-star"></i> ${item.RestRating}</small>
            </div>
            <div class="item-bottom">
                <span class="item-price">₹${item.Price_INR}</span>
                <button class="btn btn-outline btn-sm" onclick="loadRestaurantMenu('${item.RestID}', '${item.RestName}', ${item.RestRating})">View Menu</button>
            </div>
        `;
        grid.appendChild(el);
    });
}

// ---------------------------------------------------------
// Restaurant Menu Logic (Scoped View)
// ---------------------------------------------------------
async function loadRestaurantMenu(restId, restName, rating) {
    showView('view-restaurant-menu');
    state.activeRestId = restId;
    state.cart = []; // Reset cart on moving into a new restaurant
    updateCartDisplay();
    
    document.getElementById('active-rest-name').textContent = restName;
    document.getElementById('active-rest-rating').innerHTML = `<i class="fa-solid fa-star"></i> ${rating}`;
    
    try {
        const res = await fetch(`${API_BASE}/restaurants/${restId}/items`);
        const data = await res.json();
        renderMenuGrid(data);
    } catch(e) {
        console.error("Failed loading menu", e);
    }
}

// Maintain local copy of items for the cart referencing
let currentMenuReference = {};

function renderMenuGrid(items) {
    const grid = document.getElementById('menu-grid');
    grid.innerHTML = '';
    currentMenuReference = {};
    
    items.forEach(item => {
        currentMenuReference[item.ItemID] = item;
        
        const typeIcon = item.Is_Veg ? '<i class="fa-solid fa-leaf" style="color: #22c55e;"></i>' : '<i class="fa-solid fa-drumstick-bite" style="color: #ef4444;"></i>';
        const el = document.createElement('div');
        el.className = 'item-card';
        el.innerHTML = `
            <div class="item-header">
                <span class="item-type">${typeIcon}</span>
                <span class="item-category ${item.Size === 'High' ? 'tag-high' : item.Size === 'Low' ? 'tag-low' : ''}">${item.Size}</span>
            </div>
            <h4 class="item-name">${item.Name}</h4>
            <span class="item-desc text-muted">${item.Category}</span>
            <div class="item-bottom">
                <span class="item-price">₹${item.Price_INR}</span>
                <button class="add-btn" onclick="addToCart('${item.ItemID}')">Add</button>
            </div>
        `;
        grid.appendChild(el);
    });
}

// ---------------------------------------------------------
// Cart & AI Logic (Scoped)
// ---------------------------------------------------------
function addToCart(itemId) {
    const item = currentMenuReference[itemId];
    if(item) {
        state.cart.push(item);
        updateCartDisplay();
        fetchRecommendations(); // AI call scoped to active restaurant
    }
}

function removeFromCart(index) {
    state.cart.splice(index, 1);
    updateCartDisplay();
    fetchRecommendations();
}

function updateCartDisplay() {
    const cartList = document.getElementById('cart-items');
    cartList.innerHTML = '';
    state.cartTotal = 0;

    state.cart.forEach((item, index) => {
        state.cartTotal += item.Price_INR;
        const el = document.createElement('div');
        el.className = 'cart-item';
        el.innerHTML = `
            <div>
                <strong>${item.Name}</strong>
                <div class="text-muted">₹${item.Price_INR}</div>
            </div>
            <button class="remove-btn" onclick="removeFromCart(${index})">
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;
        cartList.appendChild(el);
    });

    document.getElementById('cart-subtotal').textContent = `₹${state.cartTotal}`;
}

async function placeOrder() {
    if(state.cart.length === 0) return;
    
    const cartIds = state.cart.map(i => i.ItemID);
    try {
        const res = await fetch(`${API_BASE}/order`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: state.userId,
                cart_items: cartIds
            })
        });
        
        if (res.ok) {
            alert("Order placed successfully!");
            state.cart = [];
            updateCartDisplay();
            document.getElementById('csao-rail').classList.add('hidden');
            showView('view-user-home'); // return to home
        } else {
            alert("Failed to place order.");
        }
    } catch(e) {
        console.error("Order failed", e);
        alert("Failed to place order.");
    }
}


let recTimeout;
function fetchRecommendations() {
    clearTimeout(recTimeout);
    
    const cartIds = state.cart.map(i => i.ItemID);
    if(cartIds.length === 0) {
        document.getElementById('csao-rail').classList.add('hidden');
        return;
    }

    document.getElementById('csao-rail').classList.remove('hidden');
    document.getElementById('csao-items').innerHTML = '<div class="loader">Computing pairings...</div>';

    recTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`${API_BASE}/recommend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: state.userId,
                    session_id: 'S001',
                    cart_items: cartIds,
                    restaurant_id: state.activeRestId, // SCALING FIX: Binds DLRM logic to active restaurant!
                    lat: 0,
                    lon: 0
                })
            });

            if(response.ok) {
                const data = await response.json();
                renderRecommendations(data.recommendations, data.explanations || [], data.trending || []);
            }
        } catch(e) {
            console.error('Recommendation fetch failed', e);
        }
    }, 400);
}

function renderRecommendations(recs, explanations, trendings) {
    const container = document.getElementById('csao-items');
    container.innerHTML = '';
    
    if(!recs || recs.length === 0) {
        document.getElementById('csao-rail').classList.add('hidden');
        return;
    }

    recs.forEach((rec, idx) => {
        currentMenuReference[rec.ItemID] = rec;
        const reason = explanations[idx] || "Perfect pairing!";
        const isTrending = trendings[idx] ? '<span class="tag trending-tag"><i class="fa-solid fa-fire"></i> Trending</span>' : '';
        
        const el = document.createElement('div');
        el.className = 'csao-card';
        el.innerHTML = `
            <div class="csao-reject" onclick="rejectRecommendation('${rec.ItemID}', this)" title="Not interested">
                <i class="fa-solid fa-xmark"></i>
            </div>
            <div class="csao-info">
                <strong>${rec.Name} ${isTrending}</strong>
                <span class="csao-price">₹${rec.Price_INR}</span>
                <div class="csao-ai-reason"><i class="fa-solid fa-sparkles"></i> ${reason}</div>
            </div>
            <button class="csao-add" onclick="addToCart('${rec.ItemID}')">
                <i class="fa-solid fa-plus"></i>
            </button>
        `;
        container.appendChild(el);
    });
}

async function rejectRecommendation(itemId, elementNode) {
    if(elementNode && elementNode.parentElement) elementNode.parentElement.style.display = 'none';
    try {
        await fetch(`${API_BASE}/reject`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: state.userId, item_id: itemId})
        });
        fetchRecommendations(); // Refresh rail to replace skipped item
    } catch(e) {}
}

// ---------------------------------------------------------
// Restaurant Dashboard Logic (CRUD)
// ---------------------------------------------------------
async function loadOwnerDashboard() {
    showView('view-owner-dashboard');
    try {
        const res = await fetch(`${API_BASE}/restaurants/${state.userId}/items`);
        const data = await res.json();
        renderOwnerMenuTable(data);
    } catch(e) {
        console.error("Dashboard load fail", e);
    }
}

function renderOwnerMenuTable(items) {
    const tbody = document.getElementById('owner-menu-list');
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.Name}</strong></td>
            <td>${item.Category}</td>
            <td>${item.Is_Veg ? '🟩 Veg' : '🟥 Non-Veg'}</td>
            <td>₹${item.Price_INR}</td>
            <td>
                <button class="btn btn-outline btn-sm text-primary" onclick="openEditModal('${item.ItemID}')">
                    <i class="fa-solid fa-pen"></i> Edit
                </button>
                <button class="btn btn-outline btn-sm text-danger" onclick="deleteItem('${item.ItemID}')">
                    <i class="fa-solid fa-trash"></i> Delete
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function deleteItem(itemId) {
    if(confirm("Are you sure you want to delete this specific item?")) {
        try {
            await fetch(`${API_BASE}/items/${itemId}`, { method: 'DELETE' });
            loadOwnerDashboard(); // Refresh
        } catch(e) {}
    }
}

function openCreateModal() { document.getElementById('create-modal').classList.remove('hidden'); }
function closeModal() { document.getElementById('create-modal').classList.add('hidden'); }

async function submitNewItem() {
    const payload = {
        Name: document.getElementById('new-item-name').value,
        Price_INR: parseInt(document.getElementById('new-item-price').value),
        Category: document.getElementById('new-item-category').value,
        Is_Veg: document.getElementById('new-item-veg').value === "true",
        Size: "Medium"
    };
    
    try {
        await fetch(`${API_BASE}/items/${state.userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        closeModal();
        loadOwnerDashboard();
    } catch(e) { alert("Failed to create"); }
}

let editingItemId = null;

async function openEditModal(itemId) {
    editingItemId = itemId;
    // Find item data
    try {
        const res = await fetch(`${API_BASE}/restaurants/${state.userId}/items`);
        const data = await res.json();
        const item = data.find(i => i.ItemID === itemId);
        if (item) {
            document.getElementById('edit-item-name').value = item.Name;
            document.getElementById('edit-item-price').value = item.Price_INR;
            document.getElementById('edit-item-category').value = item.Category;
            document.getElementById('edit-item-veg').value = item.Is_Veg.toString();
            document.getElementById('edit-modal').classList.remove('hidden');
        }
    } catch(e) { console.error("Could not fetch item to edit"); }
}

function closeEditModal() { 
    document.getElementById('edit-modal').classList.add('hidden'); 
    editingItemId = null;
}

async function submitEditItem() {
    if (!editingItemId) return;

    const payload = {
        Name: document.getElementById('edit-item-name').value,
        Price_INR: parseInt(document.getElementById('edit-item-price').value),
        Category: document.getElementById('edit-item-category').value,
        Is_Veg: document.getElementById('edit-item-veg').value === "true",
        Size: "Medium"
    };
    
    try {
        await fetch(`${API_BASE}/items/${editingItemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        closeEditModal();
        loadOwnerDashboard();
    } catch(e) { alert("Failed to update"); }
}

// Initialize on load
window.addEventListener('DOMContentLoaded', init);
