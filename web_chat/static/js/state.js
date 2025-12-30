// ==================== 状态管理 ====================

// 全局状态
window.appState = {
    currentModel: null,
    isSending: false,
    modelHistories: {},
    modelInfoCache: {}, // 缓存模型信息（包括 icon）
};

// 状态更新辅助函数
window.appState.setCurrentModel = function(model) {
    this.currentModel = model;
    if (model) {
        localStorage.setItem('currentModel', model);
    }
};

window.appState.getModelHistory = function(model) {
    if (!this.modelHistories[model]) {
        this.modelHistories[model] = [];
    }
    return this.modelHistories[model];
};

window.appState.addMessageToHistory = function(model, role, content) {
    if (!this.modelHistories[model]) {
        this.modelHistories[model] = [];
    }
    this.modelHistories[model].push({ role, content });
};

window.appState.clearHistory = function(model) {
    this.modelHistories[model] = [];
};
