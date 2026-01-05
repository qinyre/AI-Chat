// ==================== 状态管理 ====================

// LocalStorage 键名常量
const STORAGE_KEYS = {
    CURRENT_MODEL: 'ai_nexus_current_model',
    MODEL_HISTORIES: 'ai_nexus_model_histories'
};

// 全局状态
window.appState = {
    currentModel: null,
    isSending: false,
    modelHistories: {},
    modelInfoCache: {}, // 缓存模型信息（包括 icon）
    abortController: null, // 用于中断 AI 输出
};

/**
 * 保存对话历史到 LocalStorage
 */
window.appState.saveToLocalStorage = function() {
    try {
        const data = {
            currentModel: this.currentModel,
            modelHistories: this.modelHistories
        };
        localStorage.setItem(STORAGE_KEYS.MODEL_HISTORIES, JSON.stringify(data));
        console.debug('已保存对话历史到 LocalStorage');
    } catch (error) {
        console.error('保存对话历史失败:', error);
    }
};

/**
 * 从 LocalStorage 加载对话历史
 */
window.appState.loadFromLocalStorage = function() {
    try {
        const savedData = localStorage.getItem(STORAGE_KEYS.MODEL_HISTORIES);
        if (savedData) {
            const data = JSON.parse(savedData);
            this.modelHistories = data.modelHistories || {};
            this.currentModel = data.currentModel || null;
            console.debug('已从 LocalStorage 加载对话历史');
            return true;
        }
        return false;
    } catch (error) {
        console.error('加载对话历史失败:', error);
        return false;
    }
};

/**
 * 清除 LocalStorage 中的对话历史
 */
window.appState.clearLocalStorage = function() {
    try {
        localStorage.removeItem(STORAGE_KEYS.MODEL_HISTORIES);
        localStorage.removeItem(STORAGE_KEYS.CURRENT_MODEL);
        console.debug('已清除 LocalStorage 中的对话历史');
    } catch (error) {
        console.error('清除对话历史失败:', error);
    }
};

// 状态更新辅助函数
window.appState.setCurrentModel = function(model) {
    this.currentModel = model;
    if (model) {
        localStorage.setItem(STORAGE_KEYS.CURRENT_MODEL, model);
    }
    this.saveToLocalStorage(); // 切换模型时保存状态
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
    this.saveToLocalStorage(); // 添加消息后自动保存
};

window.appState.clearHistory = function(model) {
    this.modelHistories[model] = [];
    this.saveToLocalStorage(); // 清空历史后自动保存
};

// 页面加载时自动恢复对话历史
window.addEventListener('load', () => {
    window.appState.loadFromLocalStorage();
});

// 页面卸载前保存对话历史
window.addEventListener('beforeunload', () => {
    window.appState.saveToLocalStorage();
});
