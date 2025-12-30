// ==================== 图标管理 ====================

// Model icons configuration - Using local SVG files from assets/icons/
const modelIcons = {
    'gemini': { src: '/assets/icons/gemini_logo.svg', class: 'gemini' },
    'google': { src: '/assets/icons/gemini_logo.svg', class: 'gemini' },
    'deepseek': { src: '/assets/icons/deepseek_logo.svg', class: 'deepseek' },
    'moonshot': { src: '/assets/icons/kimi_logo.svg', class: 'kimi' },
    'kimi': { src: '/assets/icons/kimi_logo.svg', class: 'kimi' },
    'qwen': { src: '/assets/icons/qwen_logo.svg', class: 'qwen' },
    'tongyi': { src: '/assets/icons/qwen_logo.svg', class: 'qwen' },
    'spark': { src: '/assets/icons/spark_logo.svg', class: 'spark' },
    'xinghuo': { src: '/assets/icons/spark_logo.svg', class: 'spark' }
};

// 获取模型图标 URL
function getModelIconUrl(modelName) {
    // 优先使用缓存的模型信息
    if (window.appState.modelInfoCache[modelName] && window.appState.modelInfoCache[modelName].icon) {
        return getIconSrc(window.appState.modelInfoCache[modelName].icon, modelName);
    }

    // 回退到硬编码的默认映射
    const name = modelName.toLowerCase();
    if (name === 'google' || name.includes('gemini')) return '/assets/icons/gemini_logo.svg';
    if (name === 'deepseek' || name.includes('deepseek')) return '/assets/icons/deepseek_logo.svg';
    if (name === 'moonshot' || name === 'kimi' || name.includes('moonshot') || name.includes('kimi')) return '/assets/icons/kimi_logo.svg';
    if (name === 'qwen' || name.includes('qwen') || name.includes('tongyi')) return '/assets/icons/qwen_logo.svg';
    if (name === 'spark' || name.includes('spark') || name.includes('xinghuo')) return '/assets/icons/spark_logo.svg';
    return '/assets/icons/gemini_logo.svg';
}

// 获取模型图标背景色类
function getModelIconBgClass(modelName) {
    const name = modelName.toLowerCase();
    if (name === 'google' || name.includes('gemini')) return 'gemini';
    if (name === 'deepseek' || name.includes('deepseek')) return 'deepseek';
    if (name === 'moonshot' || name === 'kimi' || name.includes('moonshot') || name.includes('kimi')) return 'kimi';
    if (name === 'qwen' || name.includes('qwen') || name.includes('tongyi')) return 'qwen';
    if (name === 'spark' || name.includes('spark') || name.includes('xinghuo')) return 'spark';
    return 'gemini';
}

// Get icon CSS class for model (background gradient)
function getModelIconClass(modelName) {
    return getModelIconBgClass(modelName);
}

// Get icon key for model
function getModelIconKey(modelName) {
    return getModelIconBgClass(modelName);
}

// 根据图标字段获取图标URL
function getIconSrc(iconField, modelId) {
    if (!iconField) {
        return '/assets/icons/gemini_logo.svg';
    }

    // data URL（自定义上传的 base64 图片）
    if (iconField.startsWith('data:')) {
        return iconField;
    }

    // 完整 URL（http/https）
    if (iconField.startsWith('http')) {
        return iconField;
    }

    // 本地文件名（包含扩展名）
    if (iconField.includes('.')) {
        return `/assets/icons/${iconField}`;
    }

    return '/assets/icons/gemini_logo.svg';
}

// 获取图标颜色类（用于背景渐变）
function getIconColorClass(modelId) {
    return getModelIconBgClass(modelId);
}
