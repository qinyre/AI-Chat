// ==================== API 密钥配置管理 ====================

// 模型配置映射
const apiModelConfigs = {
    'google': {
        name: 'Google Gemini',
        iconClass: 'gemini',
        placeholder: 'AIzaSy...',
        keyName: 'GOOGLE_API_KEY'
    },
    'deepseek': {
        name: 'DeepSeek',
        iconClass: 'deepseek',
        placeholder: 'sk-...',
        keyName: 'DEEPSEEK_API_KEY'
    },
    'moonshot': {
        name: 'Moonshot/Kimi',
        iconClass: 'kimi',
        placeholder: 'sk-...',
        keyName: 'MOONSHOT_API_KEY'
    },
    'qwen': {
        name: 'Qwen (通义千问)',
        iconClass: 'qwen',
        placeholder: 'sk-...',
        keyName: 'QWEN_API_KEY'
    },
    'spark': {
        name: 'Spark (讯飞星火)',
        iconClass: 'spark',
        placeholder: 'Bearer...',
        keyName: 'SPARK_API_KEY'
    }
};

// 从后端 API 加载 API 密钥
async function loadApiKeys() {
    try {
        const response = await fetch('/api/config/load');
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {
        console.error('Failed to load API keys:', e);
    }
    return {};
}

// 保存 API 密钥到后端
async function saveApiKeys(apiKeys) {
    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(apiKeys)
        });
        return response.ok;
    } catch (e) {
        console.error('Failed to save API keys:', e);
        return false;
    }
}

// 获取当前存储的 API 密钥
async function getStoredApiKeys() {
    return await loadApiKeys();
}

// 生成 API 配置模态框内容
async function renderApiConfigModal() {
    const container = document.getElementById('api-config-list');
    const storedKeys = await loadApiKeys();

    container.innerHTML = Object.entries(apiModelConfigs).map(([modelId, config]) => {
        const hasKey = storedKeys[config.keyName] && storedKeys[config.keyName].length > 0;
        const maskedKey = hasKey ? '•'.repeat(Math.min(storedKeys[config.keyName].length, 32)) : '';

        return `
            <div class="api-config-item" data-model="${modelId}">
                <div class="api-config-label">
                    <div class="api-config-name">
                        <div class="api-config-model-icon ${config.iconClass}">
                            <svg fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"/>
                            </svg>
                        </div>
                        <span>${config.name}</span>
                    </div>
                    <div class="api-config-status ${hasKey ? 'configured' : 'unconfigured'}">
                        <span class="status-indicator"></span>
                        ${hasKey ? '已配置' : '未配置'}
                    </div>
                </div>
                <div class="api-key-input-wrapper">
                    <input
                        type="password"
                        class="api-key-input"
                        data-key="${config.keyName}"
                        placeholder="${config.placeholder}"
                        value="${maskedKey}"
                        data-actual-value="${hasKey ? storedKeys[config.keyName] : ''}"
                    >
                    <button class="api-key-toggle" type="button" title="显示/隐藏">
                        <svg class="eye-icon" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        <svg class="eye-off-icon" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="display: none;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // 绑定事件
    bindApiConfigEvents();
}

// 绑定 API 配置模态框事件
function bindApiConfigEvents() {
    // 显示/隐藏密码
    document.querySelectorAll('.api-key-toggle').forEach(btn => {
        btn.addEventListener('click', function (e) {
            // 阻止事件冒泡，避免触发 input 的 blur
            e.preventDefault();

            const input = this.parentElement.querySelector('.api-key-input');
            const eyeIcon = this.querySelector('.eye-icon');
            const eyeOffIcon = this.querySelector('.eye-off-icon');

            // 确保 actualValue 是最新的
            if (input.type === 'text') {
                // 当前是显示状态，切换到隐藏
                // 先保存当前值到 actualValue
                if (input.value && !input.value.startsWith('•')) {
                    input.dataset.actualValue = input.value;
                }
                input.type = 'password';
                eyeIcon.style.display = 'block';
                eyeOffIcon.style.display = 'none';
                if (input.dataset.actualValue) {
                    input.value = '•'.repeat(Math.min(input.dataset.actualValue.length, 32));
                }
            } else {
                // 当前是隐藏状态，切换到显示
                input.type = 'text';
                eyeIcon.style.display = 'none';
                eyeOffIcon.style.display = 'block';
                input.value = input.dataset.actualValue || '';
                // 显示后自动聚焦，方便用户修改
                input.focus();
            }
        });
    });

    // 输入时更新实际值
    document.querySelectorAll('.api-key-input').forEach(input => {
        input.addEventListener('input', function () {
            // 只在可见状态下更新 actualValue
            if (this.type === 'text') {
                this.dataset.actualValue = this.value;
            }
        });

        input.addEventListener('blur', function () {
            // 失去焦点时，如果是可见状态且不是点击了 toggle 按钮，则自动隐藏
            if (this.type === 'text' && this.dataset.actualValue) {
                // 延迟执行，避免与 toggle 按钮的 click 冲突
                setTimeout(() => {
                    // 检查 input 是否仍然是 text 状态（说明用户没有点击 toggle）
                    if (this.type === 'text') {
                        this.type = 'password';
                        this.value = '•'.repeat(Math.min(this.dataset.actualValue.length, 32));
                        const eyeIcon = this.parentElement.querySelector('.eye-icon');
                        const eyeOffIcon = this.parentElement.querySelector('.eye-off-icon');
                        if (eyeIcon) eyeIcon.style.display = 'block';
                        if (eyeOffIcon) eyeOffIcon.style.display = 'none';
                    }
                }, 200);
            }
        });
    });
}

// 打开 API 配置模态框
function openApiConfigModal() {
    renderApiConfigModal();
    document.getElementById('api-config-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

// 关闭 API 配置模态框
function closeApiConfigModal() {
    document.getElementById('api-config-modal').classList.remove('active');
    document.body.style.overflow = '';
}

// 保存 API 配置
async function saveApiConfig() {
    const inputs = document.querySelectorAll('.api-key-input');
    const apiKeys = {};

    inputs.forEach(input => {
        const keyName = input.dataset.key;
        const actualValue = input.dataset.actualValue || '';
        if (actualValue.trim()) {
            apiKeys[keyName] = actualValue.trim();
        }
    });

    if (await saveApiKeys(apiKeys)) {
        loadModels();
        closeApiConfigModal();
        showNotification('API 密钥配置已保存', 'success');
    } else {
        showNotification('保存失败，请重试', 'error');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'rgba(0, 255, 170, 0.2)' : type === 'error' ? 'rgba(255, 107, 157, 0.2)' : 'rgba(78, 205, 196, 0.2)'};
        border: 1px solid ${type === 'success' ? 'var(--accent-cyan)' : type === 'error' ? 'var(--accent-magenta)' : 'var(--accent-blue)'};
        border-radius: 12px;
        color: var(--text-primary);
        font-size: 14px;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 添加通知动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// 绑定 API 配置按钮事件
document.getElementById('api-config-btn').addEventListener('click', openApiConfigModal);
document.getElementById('close-api-config').addEventListener('click', closeApiConfigModal);
document.getElementById('cancel-api-config').addEventListener('click', closeApiConfigModal);
document.getElementById('save-api-config').addEventListener('click', saveApiConfig);

// 点击遮罩层关闭模态框
document.getElementById('api-config-modal').addEventListener('click', function (e) {
    if (e.target === this) {
        closeApiConfigModal();
    }
});

// 绑定模型管理按钮事件
document.getElementById('model-manager-btn').addEventListener('click', function() {
    window.location.href = '/model_manager';
});

// ESC 键关闭模态框
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeApiConfigModal();
    }
});
