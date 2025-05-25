// Application JavaScript Functions

// Copy to clipboard functionality
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        // Show copy success feedback
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check"></i> Copied';
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary');
        
        setTimeout(function() {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }, 2000);
    }).catch(function(err) {
        console.error('Copy failed: ', err);
        alert('Copy failed, please copy manually');
    });
}

// Confirm delete dialog
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete? This action cannot be undone.');
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// URL validation
function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// Execute after page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alert messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });
    
    // Add event listeners to all copy buttons
    document.querySelectorAll('.btn-copy').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            copyToClipboard(text, this);
        });
    });
    
    // Add confirmation dialog to delete buttons
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete()) {
                e.preventDefault();
            }
        });
    });
    
    // URL input validation
    document.querySelectorAll('input[type="url"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateUrl(this.value)) {
                this.classList.add('is-invalid');
                this.setCustomValidity('Please enter a valid URL');
            } else {
                this.classList.remove('is-invalid');
                this.setCustomValidity('');
            }
        });
    });
    
    // Friendly URL preview
    const nameInput = document.getElementById('name');
    const friendlyUrlPreview = document.getElementById('friendly-url-preview');
    
    if (nameInput && friendlyUrlPreview) {
        nameInput.addEventListener('input', function() {
            const friendlyUrl = this.value
                .toLowerCase()
                .replace(/[^a-z0-9\u4e00-\u9fa5]/g, '-')
                .replace(/-+/g, '-')
                .replace(/^-|-$/g, '');
            
            friendlyUrlPreview.textContent = friendlyUrl || 'auto-generated';
        });
    }
});

// Select all/deselect all functionality
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('input[name="selected_subscriptions"]');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    // Trigger check function
    if (typeof checkSelectedSubscriptions === 'function') {
        checkSelectedSubscriptions();
    }
}

// Check if any subscriptions are selected
function checkSelectedSubscriptions() {
    const checkboxes = document.querySelectorAll('input[name="selected_subscriptions"]:checked');
    const submitButton = document.querySelector('button[type="submit"]');
    
    if (submitButton) {
        submitButton.disabled = checkboxes.length === 0;
    }
}

// Dynamic load more content
function loadMore(url, container) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById(container).innerHTML += html;
        })
        .catch(error => {
            console.error('Load failed:', error);
        });
}

// Search functionality
function searchTable(input, tableId) {
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            if (cells[j].textContent.toLowerCase().includes(filter)) {
                found = true;
                break;
            }
        }
        
        row.style.display = found ? '' : 'none';
    }
} 