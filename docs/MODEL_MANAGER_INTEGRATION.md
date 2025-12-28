# 模型管理功能集成指南

## 概述

本文档说明如何将模型管理功能集成到 AI NEXUS 项目中。该功能允许用户在前端界面中添加、编辑和删除自定义 LLM 模型。

## 已创建的文件

### 1. `web_chat/models.json`
模型配置文件，包含所有模型的定义。

### 2. `web_chat/templates/model_manager.html`
模型管理弹窗界面，包含：
- API 类型选择（OpenAI 兼容、Google Gemini、HTTP+SSE、Spark）
- 基本配置表单（模型 ID、名称、标识、API Key 名称）
- 动态字段显示（根据 API 类型显示不同配置项）
- 图标选择器（预设图标 + 上传功能）

### 3. `web_chat/model_manager.py`
后端模型管理模块，提供：
- `get_all_models()` - 获取所有模型
- `add_model()` - 添加新模型
- `delete_model()` - 删除模型
- `upload_icon()` - 上传模型图标
- `register_routes(app)` - 注册路由

## 集成步骤

### 步骤 1: 更新 `app.py`

在 `web_chat/app.py` 中添加以下内容：

```python
# 在文件开头添加导入
from model_manager import register_routes

# 在 if __name__ == '__main__' 之前添加路由注册
register_routes(app)

# 添加 MODELS_FILE 路径常量
MODELS_FILE = os.path.join(os.path.dirname(__file__), 'models.json')
```

### 步骤 2: 更新 `llm_wrapper.py`

修改 `_load_configs()` 方法以支持从文件动态加载：

```python
def _get_models_file_path(self):
    """获取 models.json 文件路径"""
    return os.path.join(os.path.dirname(__file__), 'models.json')

def _load_models_from_file(self):
    """从 models.json 文件加载模型配置"""
    models_file = self._get_models_file_path()
    if not os.path.exists(models_file):
        return self._get_default_configs()

    try:
        with open(models_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        configs = {}
        for model in data.get('models', []):
            if not model.get('enabled', True):
                continue

            model_id = model['id']
            config = {
                'type': model['type'],
                'model': model['model'],
                'api_key': self.custom_api_keys.get(model['api_key_name']) or os.environ.get(model['api_key_name'], ""),
                'api_key_name': model['api_key_name'],
                'name': model.get('name', model_id),
                'icon': model.get('icon', '')
            }

            if 'base_url' in model:
                config['base_url'] = model['base_url']
            if 'url' in model:
                config['url'] = model['url']
            if 'system' in model:
                config['system'] = model['system']

            configs[model_id] = config

        return configs if configs else self._get_default_configs()

    except (json.JSONDecodeError, IOError, KeyError) as e:
        print(f'Failed to load models from file: {e}', flush=True)
        return self._get_default_configs()

def _get_default_configs(self):
    """获取默认模型配置（向后兼容）"""
    # ... 原有的配置代码 ...

def _load_configs(self):
    """加载配置，优先从文件读取"""
    return self._load_models_from_file()

def get_model_info(self, model_id):
    """获取模型详细信息"""
    return self.configs.get(model_id, {})

def get_all_models_info(self):
    """获取所有模型信息"""
    return self.configs
```

### 步骤 3: 在主页面添加模型管理入口

在 `web_chat/templates/index.html` 中添加：

```javascript
// 添加模型管理按钮事件
document.addEventListener('DOMContentLoaded', () => {
    // 在设置区域添加模型管理按钮
    const modelManagerBtn = document.createElement('button');
    modelManagerBtn.className = 'model-manager-button';
    modelManagerBtn.textContent = '⚙️ 模型管理';
    modelManagerBtn.onclick = () => {
        // 打开模型管理弹窗
        window.open('/model_manager', '_blank', 'width=800,height=700');
    };

    // 将按钮添加到设置区域
    document.querySelector('.settings-area').appendChild(modelManagerBtn);
});
```

### 步骤 4: 添加模型管理路由

在 `app.py` 中添加模型管理页面路由：

```python
@app.route('/model_manager')
def model_manager():
    return render_template('model_manager.html')
```

## API 端点说明

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/models/list` | GET | 获取所有模型列表 |
| `/api/models` | POST | 添加新模型 |
| `/api/models/<id>` | DELETE | 删除指定模型 |
| `/api/models/icon/upload` | POST | 上传模型图标 |

## API 类型说明

### OpenAI 兼容
- 需要字段：`base_url`, `model`
- 支持系统提示词：是
- 支持对话历史：是

### Google Gemini
- 需要字段：`model`
- 支持系统提示词：否
- 支持对话历史：是

### HTTP + SSE
- 需要字段：`url`, `model`
- 支持系统提示词：否
- 支持对话历史：是

### Spark 特殊格式
- 需要字段：`url`, `model`
- 支持系统提示词：否
- 支持对话历史：否

## 测试清单

- [ ] 启动应用后访问 `/model_manager` 页面
- [ ] 添加一个新的 OpenAI 兼容模型
- [ ] 添加一个新的 HTTP+SSE 模型
- [ ] 上传自定义模型图标
- [ ] 删除一个自定义模型
- [ ] 尝试删除内置模型（应该被拒绝）
- [ ] 在主界面使用新添加的模型进行对话

## 注意事项

1. **内置模型保护**：google、deepseek、moonshot、qwen、spark 这 5 个内置模型不能被删除

2. **API 密钥安全**：自定义模型的 API 密钥需要在环境变量或前端配置中设置

3. **图标文件**：上传的图标会保存到 `web_chat/assets/icons/` 目录

4. **向后兼容**：如果 `models.json` 不存在，系统会使用默认配置

## 故障排除

### 问题：模型添加后无法使用
**解决方案**：检查 API Key 是否正确配置，确保环境变量或前端配置中存在对应的密钥

### 问题：图标上传失败
**解决方案**：检查 `web_chat/assets/icons/` 目录是否存在且有写入权限

### 问题：模型列表不显示新添加的模型
**解决方案**：刷新页面或重启应用，因为模型配置在启动时加载

---

**生成时间**: 2025-12-28
**版本**: 1.0.0
