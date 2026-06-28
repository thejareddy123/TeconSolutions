// ============================================================
// static/js/main.js
// Common JavaScript functions used across all pages
// ============================================================


// ============================================================
// SIDEBAR TOGGLE (for mobile)
// ============================================================
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar.classList.contains('-translate-x-full')) {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
    }
}


// ============================================================
// TOAST NOTIFICATIONS
// Show success/error messages at bottom of screen
// ============================================================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastInner = document.getElementById('toastInner');
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg = document.getElementById('toastMsg');
    
    // Set message
    toastMsg.textContent = message;
    
    // Set color and icon based on type
    if (type === 'success') {
        toastInner.className = 'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium bg-green-600';
        toastIcon.className = 'fas fa-check-circle';
    } else if (type === 'error') {
        toastInner.className = 'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium bg-red-600';
        toastIcon.className = 'fas fa-exclamation-circle';
    } else if (type === 'warning') {
        toastInner.className = 'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium bg-amber-600';
        toastIcon.className = 'fas fa-exclamation-triangle';
    } else {
        toastInner.className = 'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium bg-blue-600';
        toastIcon.className = 'fas fa-info-circle';
    }
    
    // Show toast
    toast.classList.remove('hidden');
    toast.classList.add('flex');
    
    // Hide after 4 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
        toast.classList.remove('flex');
    }, 4000);
}


// ============================================================
// MODAL HELPERS
// ============================================================
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scroll
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    document.body.style.overflow = '';
}

// Close modal when clicking the overlay
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.add('hidden');
        document.body.style.overflow = '';
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => {
            m.classList.add('hidden');
            document.body.style.overflow = '';
        });
    }
});


// ============================================================
// API HELPERS
// Simple fetch wrappers for common patterns
// ============================================================

// Send a POST request with form data
async function postForm(url, formElement) {
    const formData = new FormData(formElement);
    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });
    return response.json();
}

// Send a POST request with JSON data
async function postJson(url, data = {}) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            formData.append(key, value);
        }
    });
    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });
    return response.json();
}

// Standard button handler - shows loading state
async function submitAction(url, data, successMessage, onSuccess) {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<span class="spinner"></span> Loading...';
    btn.disabled = true;
    
    try {
        const result = await postJson(url, data);
        
        if (result.success) {
            showToast(successMessage || result.message, 'success');
            if (onSuccess) onSuccess(result);
        } else {
            showToast(result.error || 'Something went wrong', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
        console.error(err);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}


// ============================================================
// NOTIFICATIONS DROPDOWN
// ============================================================
let notifLoaded = false;

function toggleNotifications() {
    const dropdown = document.getElementById('notifDropdown');
    dropdown.classList.toggle('hidden');
    
    // Load notifications once
    if (!notifLoaded) {
        loadNotifications();
        notifLoaded = true;
    }
}

async function loadNotifications() {
    try {
        const response = await fetch('/notifications/');
        const data = await response.json();
        
        const list = document.getElementById('notifList');
        
        if (!data.notifications || data.notifications.length === 0) {
            list.innerHTML = '<div class="text-center text-gray-400 py-8 text-sm"><i class="fas fa-bell-slash mb-2 text-2xl block"></i>No notifications</div>';
            return;
        }
        
        list.innerHTML = data.notifications.map(n => `
            <div class="px-4 py-3 hover:bg-gray-50 border-b border-gray-100 cursor-pointer ${!n.is_read ? 'bg-blue-50' : ''}"
                 onclick="markNotifRead(${n.id}, '${n.link || '/dashboard'}')">
                <p class="text-sm font-medium text-gray-800">${escapeHtml(n.title)}</p>
                <p class="text-xs text-gray-500 mt-0.5 truncate">${escapeHtml(n.message)}</p>
                <p class="text-xs text-gray-400 mt-1">${formatDate(n.created_at)}</p>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load notifications:', e);
    }
}

async function markNotifRead(id, link) {
    await fetch(`/notifications/${id}/read`, { method: 'POST' });
    window.location.href = link;
}

async function markAllRead() {
    await fetch('/notifications/mark-all-read', { method: 'POST' });
    document.getElementById('notifDropdown').classList.add('hidden');
    // Remove the badge
    const badge = document.querySelector('.notification-badge');
    if (badge) badge.remove();
    showToast('All notifications marked as read', 'success');
}

// Close notification dropdown when clicking outside
document.addEventListener('click', function(e) {
    const dropdown = document.getElementById('notifDropdown');
    const bell = e.target.closest('[onclick="toggleNotifications()"]');
    if (dropdown && !dropdown.contains(e.target) && !bell) {
        dropdown.classList.add('hidden');
    }
});


// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function escapeHtml(text) {
    if (!text) return '';
    return text.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}

function formatDatetime(dateStr) {
    if (!dateStr) return '';
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        });
    } catch (e) {
        return dateStr;
    }
}

// Confirm before deleting
function confirmAction(message, callback) {
    if (window.confirm(message)) {
        callback();
    }
}

// Show/hide password toggle
function togglePassword(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        input.type = 'password';
        btn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Debounce function (for search inputs)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
