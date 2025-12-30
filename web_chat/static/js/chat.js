// ==================== 聊天功能 ====================

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

    try {
        const response = await fetch('/api/chat', {
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

        contentDiv.innerHTML = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            fullText += chunk;
            contentDiv.innerHTML = marked.parse(fullText);
            // 代码语法高亮
            contentDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

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
            contentDiv.innerHTML = `<span style="color: var(--accent-magenta);">Error: ${err.message}</span>`;
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
        content.innerHTML = text ? marked.parse(text) : '';
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

// 清空对话历史
function clearHistory() {
    if (!window.appState.currentModel) return;
    window.appState.clearHistory(window.appState.currentModel);
    const iconUrl = getModelIconUrl(window.appState.currentModel);
    const iconBgClass = getModelIconBgClass(window.appState.currentModel);
    chatContainer.innerHTML = `
        <div class="welcome-state">
            <div class="welcome-icon ${iconBgClass}">
                <img src="${iconUrl}" style="width:48px;height:48px;" alt="${window.appState.currentModel}">
            </div>
            <h1 class="welcome-title">与 ${window.appState.currentModel.toUpperCase()} 对话</h1>
            <p class="welcome-subtitle">输入你的问题，AI 将实时为你解答</p>
        </div>`;
}

// Button events
sendBtn.addEventListener('click', handleSendBtnClick);
document.getElementById('clear-btn').addEventListener('click', clearHistory);
