// Placement Management System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initAlerts();
    initForms();
    initTables();
    initNavigation();
});

// Auto-dismiss alerts after 5 seconds
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// Form validation and enhancement
function initForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    
                    // Add error message if not exists
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('span');
                        errorMsg.className = 'error-message';
                        errorMsg.style.color = '#ef4444';
                        errorMsg.style.fontSize = '0.875rem';
                        errorMsg.textContent = 'This field is required';
                        field.parentNode.insertBefore(errorMsg, field.nextSibling);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.hasAttribute('required') && !this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            });
        });
    });
}

// Table functionality
function initTables() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        // Add sorting functionality
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(table, index));
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAsc = table.querySelectorAll('th')[columnIndex].classList.contains('asc');
    
    // Remove previous sorting classes
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('asc', 'desc');
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (isAsc) {
            return bText.localeCompare(aText);
        } else {
            return aText.localeCompare(bText);
        }
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
    
    // Update header class
    table.querySelectorAll('th')[columnIndex].classList.add(isAsc ? 'desc' : 'asc');
}

// Navigation enhancement
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// API calls
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching stats:', error);
        return null;
    }
}

// Update application status
async function updateApplicationStatus(appId, status) {
    try {
        const response = await fetch(`/update_application/${appId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `status=${status}`
        });
        
        if (response.ok) {
            location.reload();
        } else {
            alert('Error updating status');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Search functionality
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('keyup', function() {
        const filter = input.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

// Modal functionality
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Confirm delete
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Show loading state
function showLoading(button) {
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '⏳ Loading...';
    button.disabled = true;
}

function hideLoading(button) {
    button.innerHTML = button.dataset.originalText;
    button.disabled = false;
}

// Export functions for use in other scripts
window.PMS = {
    fetchStats,
    updateApplicationStatus,
    searchTable,
    openModal,
    closeModal,
    confirmDelete,
    formatDate,
    showLoading,
    hideLoading
};