// ==================== 聊天功能 ====================

/**
 * HTML 转义函数，防止 XSS 攻击
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== 错误处理系统 ====================

/**
 * 错误类型枚举
 */
const ErrorType = {
    NETWORK: 'network',           // 网络连接错误
    API_KEY: 'api_key',           // API 密钥无效或缺失
    RATE_LIMIT: 'rate_limit',     // 速率限制
    TIMEOUT: 'timeout',           // 请求超时
    SERVER_ERROR: 'server_error', // 服务器错误
    UNKNOWN: 'unknown'            // 未知错误
};

/**
 * 错误消息映射
 * 每种错误类型包含：title（标题）、message（描述）、icon（图标）、solution（解决建议）
 */
const ERROR_MESSAGES = {
    [ErrorType.NETWORK]: {
        title: '网络连接错误',
        message: '无法连接到服务器，请检查网络连接',
        icon: '🌐',
        solution: '建议：\n1. 检查网络连接是否正常\n2. 确认可以访问外网\n3. 稍后重试'
    },
    [ErrorType.API_KEY]: {
        title: 'API 密钥错误',
        message: 'API 密钥无效或未配置',
        icon: '🔑',
        solution: '建议：\n1. 点击设置图标打开 API 配置\n2. 检查对应模型的 API 密钥是否正确\n3. 重新配置密钥后重试'
    },
    [ErrorType.RATE_LIMIT]: {
        title: '请求过于频繁',
        message: '已超过 API 速率限制',
        icon: '⏱️',
        solution: '建议：\n1. 等待一段时间后重试\n2. 降低请求频率\n3. 如需更高限制，请联系管理员'
    },
    [ErrorType.TIMEOUT]: {
        title: '请求超时',
        message: '服务器响应时间过长',
        icon: '⏰',
        solution: '建议：\n1. 检查网络连接速度\n2. 稍后重试\n3. 尝试缩短问题长度'
    },
    [ErrorType.SERVER_ERROR]: {
        title: '服务器错误',
        message: '服务器处理请求时出错',
        icon: '⚠️',
        solution: '建议：\n1. 稍后重试\n2. 如果问题持续，请联系技术支持'
    },
    [ErrorType.UNKNOWN]: {
        title: '未知错误',
        message: '发生了意外错误',
        icon: '❓',
        solution: '建议：\n1. 刷新页面重试\n2. 检查浏览器控制台获取详细错误信息\n3. 联系技术支持'
    }
};

/**
 * 分析错误并返回错误类型
 * @param {Error} error - 错误对象
 * @param {Response} response - 可选的响应对象
 * @returns {string} 错误类型
 */
function classifyError(error, response = null) {
    // 检查错误名称和消息
    if (error.name === 'AbortError') {
        return 'ABORTED'; // 用户主动中断，特殊处理
    }

    const errorMessage = error.message?.toLowerCase() || '';
    const errorName = error.name?.toLowerCase() || '';

    // 网络错误
    if (errorName === 'networkerror' ||
        errorMessage.includes('network') ||
        errorMessage.includes('fetch')) {
        return ErrorType.NETWORK;
    }

    // 超时错误
    if (errorMessage.includes('timeout') ||
        errorName === 'timeouterror') {
        return ErrorType.TIMEOUT;
    }

    // 检查 HTTP 状态码
    if (response) {
        const status = response.status;

        // 401 Unauthorized - API 密钥错误
        if (status === 401 || status === 403) {
            return ErrorType.API_KEY;
        }

        // 429 Too Many Requests - 速率限制
        if (status === 429) {
            return ErrorType.RATE_LIMIT;
        }

        // 5xx 服务器错误
        if (status >= 500) {
            return ErrorType.SERVER_ERROR;
        }
    }

    // API 密钥相关错误消息
    if (errorMessage.includes('api') ||
        errorMessage.includes('key') ||
        errorMessage.includes('unauthorized') ||
        errorMessage.includes('authentication')) {
        return ErrorType.API_KEY;
    }

    // 默认为未知错误
    return ErrorType.UNKNOWN;
}

/**
 * 获取用户友好的错误消息
 * @param {string} errorType - 错误类型
 * @param {Error} error - 原始错误对象
 * @returns {string} 格式化的错误消息
 */
function getFriendlyErrorMessage(errorType, error = null) {
    const errorInfo = ERROR_MESSAGES[errorType] || ERROR_MESSAGES[ErrorType.UNKNOWN];

    let message = `${errorInfo.icon} ${errorInfo.title}\n\n${errorInfo.message}`;

    // 如果有解决方案，添加解决方案
    if (errorInfo.solution) {
        message += `\n\n${errorInfo.solution}`;
    }

    // 调试模式下显示原始错误信息
    if (error && error.message) {
        message += `\n\n[调试信息] ${error.message}`;
    }

    return message;
}

/**
 * 显示错误通知
 * @param {string} errorType - 错误类型
 * @param {Error} error - 原始错误对象
 */
function showErrorNotification(errorType, error = null) {
    const errorInfo = ERROR_MESSAGES[errorType] || ERROR_MESSAGES[ErrorType.UNKNOWN];
    const message = `${errorInfo.icon} ${errorInfo.title}: ${errorInfo.message}`;
    showNotification(message, 'error');
}

/**
 * 创建错误消息 HTML（用于聊天界面）
 * @param {string} errorType - 错误类型
 * @param {Error} error - 原始错误对象
 * @returns {string} HTML 字符串
 */
function createErrorMessageHtml(errorType, error = null) {
    const errorInfo = ERROR_MESSAGES[errorType] || ERROR_MESSAGES[ErrorType.UNKNOWN];

    return `
        <div style="display: flex; align-items: start; gap: 12px; padding: 16px; background: rgba(255, 107, 157, 0.1); border: 1px solid rgba(255, 107, 157, 0.3); border-radius: 12px;">
            <div style="font-size: 24px; flex-shrink: 0;">${errorInfo.icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">${errorInfo.title}</div>
                <div style="color: var(--text-secondary); font-size: 14px; line-height: 1.5;">${errorInfo.message}</div>
                ${errorInfo.solution ? `<div style="margin-top: 8px; padding: 8px 12px; background: rgba(255, 107, 157, 0.1); border-radius: 8px; font-size: 13px; color: var(--text-secondary); white-space: pre-line;">${errorInfo.solution}</div>` : ''}
            </div>
        </div>
    `;
}

// DOM Elements
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatContainer = document.getElementById('chat-container');

// Auto resize textarea
input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// Keyboard shortcuts
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendBtnClick();
    }
});

// 按钮点击事件处理（发送或中断）
function handleSendBtnClick() {
    if (window.appState.isSending) {
        abortGeneration();
    } else {
        sendMessage();
    }
}

// 中断 AI 生成
function abortGeneration() {
    if (window.appState.abortController) {
        window.appState.abortController.abort();
        window.appState.abortController = null;
    }
    window.appState.isSending = false;
    updateSendButtonState(false);
}

// 更新发送按钮状态
function updateSendButtonState(isSending) {
    if (isSending) {
        // 切换为中断按钮
        sendBtn.classList.add('stop-mode');
        sendBtn.innerHTML = `
            <svg fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h12v12H6z" />
            </svg>
        `;
        sendBtn.disabled = false;
    } else {
        // 恢复为发送按钮
        sendBtn.classList.remove('stop-mode');
        sendBtn.innerHTML = `
            <svg fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round"
                    d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
        `;
        sendBtn.disabled = false;
    }
}

// 发送消息
async function sendMessage() {
    if (window.appState.isSending) return;
    window.appState.isSending = true;
    updateSendButtonState(true);

    const text = input.value.trim();
    if (!text) {
        window.appState.isSending = false;
        updateSendButtonState(false);
        return;
    }
    if (!window.appState.currentModel) {
        window.appState.isSending = false;
        updateSendButtonState(false);
        return;
    }

    input.value = '';
    input.style.height = 'auto';

    const history = window.appState.getModelHistory(window.appState.currentModel);
    if (history.length === 0) {
        chatContainer.innerHTML = '';
    }

    addMessage('user', text);
    window.appState.addMessageToHistory(window.appState.currentModel, 'user', text);

    const aiMsgDiv = addMessage('assistant', '');
    const contentDiv = aiMsgDiv;
    contentDiv.innerHTML = '<span class="typing-cursor"></span>';

    // 创建 AbortController 用于中断请求
    window.appState.abortController = new AbortController();

    let response = null; // 在 try 外部声明，以便 catch 中访问

    try {
        response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: window.appState.currentModel,
                messages: window.appState.getModelHistory(window.appState.currentModel),
                api_keys: await getStoredApiKeys()
            }),
            signal: window.appState.abortController.signal
        });

        if (!response.ok) throw new Error('Network error: ' + response.statusText);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let lastUpdateTime = 0;
        let pendingChunks = [];

        contentDiv.innerHTML = '';

        // 节流函数：限制 DOM 更新频率
        function shouldUpdate(now) {
            // 每 50ms 最多更新一次，或者累计了 5 个 chunk
            return now - lastUpdateTime > 50 || pendingChunks.length >= 5;
        }

        // 渲染函数
        function renderContent() {
            if (fullText.trim()) {
                // 使用 DOMPurify 清理 HTML 以防止 XSS 攻击
                const html = DOMPurify.sanitize(marked.parse(fullText));
                contentDiv.innerHTML = html;

                // 代码语法高亮（仅在有代码块时执行）
                if (html.includes('<pre>')) {
                    contentDiv.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }

                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            lastUpdateTime = performance.now();
            pendingChunks = [];
        }

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            fullText += chunk;
            pendingChunks.push(chunk);

            const now = performance.now();

            // 检查是否应该更新 DOM
            if (shouldUpdate(now)) {
                // 使用 requestAnimationFrame 优化渲染时机
                await new Promise(resolve => requestAnimationFrame(resolve));
                renderContent();
            }
        }

        // 最终渲染（确保所有内容都被渲染）
        renderContent();

        window.appState.addMessageToHistory(window.appState.currentModel, 'assistant', fullText);
    } catch (err) {
        // 检查是否是用户主动中断
        if (err.name === 'AbortError') {
            // 保存已生成的部分内容
            const partialText = contentDiv.textContent || '';
            if (partialText) {
                window.appState.addMessageToHistory(window.appState.currentModel, 'assistant', partialText);
                // 添加中断标记
                const stopBadge = document.createElement('span');
                stopBadge.className = 'stop-badge';
                stopBadge.textContent = ' [已中断]';
                contentDiv.appendChild(stopBadge);
            } else {
                // 如果没有任何内容，移除消息
                aiMsgDiv.remove();
            }
        } else {
            // 使用新的错误分类系统
            const errorType = classifyError(err, response);

            // 在聊天界面显示详细错误信息
            const errorHtml = createErrorMessageHtml(errorType, err);
            contentDiv.innerHTML = DOMPurify.sanitize(errorHtml);

            // 显示错误通知
            showErrorNotification(errorType, err);
        }
    } finally {
        window.appState.isSending = false;
        window.appState.abortController = null;
        updateSendButtonState(false);
    }
}

// 添加消息到聊天界面
function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    if (role === 'assistant') {
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = `<svg fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width: 20px; height: 20px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
        </svg>`;
        div.appendChild(avatar);
    }

    const content = document.createElement('div');
    content.className = `message-content ${role === 'assistant' ? 'prose' : ''}`;

    if (role === 'user') {
        content.textContent = text;
    } else {
        // 使用 DOMPurify 清理 Markdown 解析后的 HTML
        content.innerHTML = text ? DOMPurify.sanitize(marked.parse(text)) : '';
        // 代码语法高亮
        content.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    div.appendChild(content);
    chatContainer.appendChild(div);

    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 0);

    return content;
}

// 清空对话历史（带确认对话框）
function clearHistory() {
    if (!window.appState.currentModel) return;

    // 显示确认对话框
    const modelName = window.appState.currentModel.toUpperCase();
    const confirmed = confirm(`确定要清空与 ${modelName} 的对话记录吗？\n\n此操作不可撤销，所有对话历史将被永久删除。`);

    if (!confirmed) return; // 用户取消

    // 用户确认，执行清空操作
    window.appState.clearHistory(window.appState.currentModel);
    const iconUrl = getModelIconUrl(window.appState.currentModel);
    const iconBgClass = getModelIconBgClass(window.appState.currentModel);
    chatContainer.innerHTML = `
        <div class="welcome-state">
            <div class="welcome-icon ${iconBgClass}">
                <img src="${iconUrl}" style="width:48px;height:48px;" alt="${window.appState.currentModel}">
            </div>
            <h1 class="welcome-title">与 ${modelName} 对话</h1>
            <p class="welcome-subtitle">输入你的问题，AI 将实时为你解答</p>
        </div>`;

    // 显示成功提示
    showNotification(`已清空 ${modelName} 的对话记录`, 'success');
}

// Button events
sendBtn.addEventListener('click', handleSendBtnClick);
document.getElementById('clear-btn').addEventListener('click', clearHistory);
