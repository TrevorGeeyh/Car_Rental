// 等待DOM完全加载后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化各种组件
    initializeComponents();
    
    // 为消息提醒设置自动关闭
    setupAlertDismiss();
    
    // 添加表单验证
    setupFormValidation();
});

/**
 * 初始化各种Bootstrap组件
 */
function initializeComponents() {
    // 初始化所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化所有弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * 设置消息提醒的自动关闭
 */
function setupAlertDismiss() {
    // 获取所有的提醒框
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    // 为每个提醒框设置定时自动关闭
    alerts.forEach(function(alert) {
        // 5秒后自动关闭提醒框
        setTimeout(function() {
            // 获取Bootstrap Alert实例并调用close方法
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * 设置表单验证
 */
function setupFormValidation() {
    // 获取所有需要验证的表单
    const forms = document.querySelectorAll('.needs-validation');
    
    // 阻止默认提交行为并进行验证
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * 动态更新租车价格计算
 * @param {number} dailyRate - 车辆日租金
 * @param {string} startDate - 开始日期（YYYY-MM-DD格式）
 * @param {string} endDate - 结束日期（YYYY-MM-DD格式）
 * @returns {number} - 计算的总价
 */
function calculateRentalPrice(dailyRate, startDate, endDate) {
    // 如果日期未选择，返回0
    if (!startDate || !endDate) return 0;
    
    // 转换为日期对象
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    // 计算天数差
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    // 至少租1天
    const days = Math.max(1, diffDays);
    
    // 计算总价
    return days * dailyRate;
}

/**
 * 日期格式化函数
 * @param {Date} date - 日期对象
 * @param {string} format - 格式字符串 (默认: 'YYYY-MM-DD')
 * @returns {string} - 格式化后的日期字符串
 */
function formatDate(date, format = 'YYYY-MM-DD') {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    let result = format;
    result = result.replace('YYYY', year);
    result = result.replace('MM', month);
    result = result.replace('DD', day);
    
    return result;
}

/**
 * 用于处理Ajax请求的通用函数
 * @param {string} url - 请求URL
 * @param {string} method - 请求方法 (GET, POST, etc.)
 * @param {Object} data - 请求数据
 * @param {function} successCallback - 成功回调函数
 * @param {function} errorCallback - 错误回调函数
 */
function ajaxRequest(url, method, data, successCallback, errorCallback) {
    // 创建XMLHttpRequest对象
    const xhr = new XMLHttpRequest();
    
    // 配置请求
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    
    // 设置回调
    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            // 请求成功
            const response = JSON.parse(xhr.responseText);
            if (successCallback) successCallback(response);
        } else {
            // 请求失败
            if (errorCallback) errorCallback(xhr.statusText);
        }
    };
    
    // 处理网络错误
    xhr.onerror = function() {
        if (errorCallback) errorCallback('网络错误');
    };
    
    // 发送请求
    xhr.send(JSON.stringify(data));
}

/**
 * 获取Cookie值
 * @param {string} name - Cookie名称
 * @returns {string} - Cookie值
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 