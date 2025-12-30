// ==================== 模型管理 ====================

// 加载模型列表
function loadModels() {
    fetch('/api/models/list')
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('model-list');
            list.innerHTML = '';

            if (!data.success || !data.models) {
                console.error('Failed to load models:', data);
                return;
            }

            const models = data.models;
            models.forEach(m => {
                if (!m.enabled) return;

                // 缓存模型信息
                window.appState.modelInfoCache[m.id] = m;

                if (!window.appState.modelHistories[m.id]) {
                    window.appState.modelHistories[m.id] = [];
                }

                // 使用 API 返回的 icon 字段
                const iconSrc = getIconSrc(m.icon, m.id);
                const iconClass = getIconColorClass(m.id);

                const btn = document.createElement('button');
                btn.className = 'model-button';
                btn.innerHTML = `
                    <div class="model-icon ${iconClass}">
                        <img src="${iconSrc}" alt="${m.id}" style="width: 24px; height: 24px;">
                    </div>
                    <div class="model-info">
                        <div class="model-name">${m.id}</div>
                        <div class="model-status">
                            <span class="status-dot"></span>
                            <span>在线</span>
                        </div>
                    </div>
                `;
                btn.onclick = () => selectModel(m.id, btn);
                list.appendChild(btn);
            });

            // 获取启用的模型ID列表
            const enabledModelIds = models.filter(m => m.enabled).map(m => m.id);

            if (enabledModelIds.length > 0 && !list.querySelector('.selected')) {
                const savedModel = localStorage.getItem('currentModel');
                const modelToSelect = enabledModelIds.includes(savedModel) ? savedModel : enabledModelIds[0];
                const targetButton = Array.from(list.children).find(
                    btn => btn.querySelector('.model-name')?.textContent === modelToSelect
                );
                selectModel(modelToSelect, targetButton || list.firstChild);
            }
        })
        .catch(err => {
            console.error('Error loading models:', err);
        });
}

// 选择模型
function selectModel(model, element) {
    window.appState.setCurrentModel(model);
    document.getElementById('current-model-name').innerText = model.toUpperCase();

    // Update active state
    document.querySelectorAll('.model-button').forEach(b => b.classList.remove('active'));
    if (element) element.classList.add('active');

    // Restore chat history
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = '';

    const history = window.appState.getModelHistory(model);
    if (history.length === 0) {
        const iconUrl = getModelIconUrl(model);
        const iconBgClass = getModelIconBgClass(model);
        chatContainer.innerHTML = `
            <div class="welcome-state">
                <div class="welcome-icon ${iconBgClass}">
                    <img src="${iconUrl}" style="width:48px;height:48px;" alt="${model}">
                </div>
                <h1 class="welcome-title">与 ${model.toUpperCase()} 对话</h1>
                <p class="welcome-subtitle">输入你的问题，AI 将实时为你解答</p>
            </div>`;
    } else {
        history.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
    }
}

// 初始加载模型
loadModels();

// 当页面重新获得可见性时重新加载模型（从模型管理页面返回时）
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        loadModels();
    }
});
