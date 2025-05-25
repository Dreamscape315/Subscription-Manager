// 应用JavaScript功能

// 复制到剪贴板功能
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        // 显示复制成功反馈
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check"></i> 已复制';
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary');
        
        setTimeout(function() {
            button.innerHTML = originalText;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }, 2000);
    }).catch(function(err) {
        console.error('复制失败: ', err);
        alert('复制失败，请手动复制');
    });
}

// 确认删除对话框
function confirmDelete(message) {
    return confirm(message || '确定要删除吗？此操作不可撤销。');
}

// 表单验证
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

// URL验证
function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏提示消息
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
    
    // 为所有复制按钮添加事件监听器
    document.querySelectorAll('.btn-copy').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            copyToClipboard(text, this);
        });
    });
    
    // 为删除按钮添加确认对话框
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete()) {
                e.preventDefault();
            }
        });
    });
    
    // URL输入框验证
    document.querySelectorAll('input[type="url"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateUrl(this.value)) {
                this.classList.add('is-invalid');
                this.setCustomValidity('请输入有效的URL');
            } else {
                this.classList.remove('is-invalid');
                this.setCustomValidity('');
            }
        });
    });
    
    // 友好URL预览
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

// 全选/取消全选功能
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('input[name="selected_subscriptions"]');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
    });
    // 触发检查函数
    if (typeof checkSelectedSubscriptions === 'function') {
        checkSelectedSubscriptions();
    }
}

// 检查是否有选中的订阅
function checkSelectedSubscriptions() {
    const checkboxes = document.querySelectorAll('input[name="selected_subscriptions"]:checked');
    const submitButton = document.querySelector('button[type="submit"]');
    
    if (submitButton) {
        submitButton.disabled = checkboxes.length === 0;
    }
}

// 动态加载更多内容
function loadMore(url, container) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById(container).innerHTML += html;
        })
        .catch(error => {
            console.error('加载失败:', error);
        });
}

// 搜索功能
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