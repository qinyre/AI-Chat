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
        sendMessage();
    }
});

// 发送消息
async function sendMessage() {
    if (window.appState.isSending) return;
    window.appState.isSending = true;
    sendBtn.disabled = true;

    const text = input.value.trim();
    if (!text) {
        window.appState.isSending = false;
        sendBtn.disabled = false;
        return;
    }
    if (!window.appState.currentModel) {
        window.appState.isSending = false;
        sendBtn.disabled = false;
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

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: window.appState.currentModel,
                messages: window.appState.getModelHistory(window.appState.currentModel),
                api_keys: await getStoredApiKeys()
            })
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
        contentDiv.innerHTML = `<span style="color: var(--accent-magenta);">Error: ${err.message}</span>`;
    } finally {
        window.appState.isSending = false;
        sendBtn.disabled = false;
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
sendBtn.addEventListener('click', sendMessage);
document.getElementById('clear-btn').addEventListener('click', clearHistory);
