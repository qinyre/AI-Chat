# README 更新内容 - 模型管理功能

## 需要添加到 README.md 的内容

### 1. 在"功能特性"部分添加"自定义模型"功能

将核心功能表格更新为：

| 功能 | 描述 |
|------|------|
| **多模型支持** | 集成 Google Gemini、DeepSeek、Moonshot/Kimi、Qwen、Spark 五大 AI 模型 |
| **自定义模型** | 支持通过前端界面添加自定义 LLM 模型 |
| **实时流式响应** | 基于 Server-Sent Events (SSE) 的流式传输，提供即时反馈 |
| **独立对话历史** | 每个模型维护独立的对话上下文，支持多轮对话 |
| **Markdown 渲染** | 支持 Markdown 格式的响应内容，包含代码高亮 |
| **主题切换** | 支持深色/浅色主题自由切换 |
| **响应式设计** | 适配桌面端和移动端设备 |

### 2. 在"使用方法"部分后添加"模型管理"小节

```
## 模型管理

### 添加自定义模型

AI NEXUS 支持添加自定义 LLM 模型，无需修改代码即可扩展支持的模型列表。

#### 支持的 API 类型

| 类型 | 说明 | 必填字段 | 支持系统提示词 |
|------|------|----------|---------------|
| **OpenAI 兼容** | 使用 OpenAI SDK 或兼容接口 | `base_url`, `model` | 是 |
| **Google Gemini** | 使用 Google GenAI SDK | `model` | 否 |
| **HTTP + SSE** | 通用 HTTP 流式接口 | `url`, `model` | 否 |
| **Spark 特殊格式** | 讯飞星火 API 格式 | `url`, `model` | 否 |

#### 添加模型步骤

1. **打开模型管理页面**
   - 访问 `/model_manager` 或从主界面点击"模型管理"按钮

2. **填写模型配置**
   - **模型 ID**: 唯一标识符（如：`gpt4`, `claude-opus`）
   - **模型名称**: 显示名称（如：`GPT-4`, `Claude Opus`）
   - **API 类型**: 选择对应的接口类型
   - **模型标识**: API 调用的模型名称（如：`gpt-4-turbo`）
   - **API Key 环境变量名**: 如 `CUSTOM_API_KEY`

3. **配置 API 参数**（根据选择的类型）
   - **OpenAI 兼容**: 填写 API 基础 URL（如：`https://api.openai.com/v1`）
   - **HTTP + SSE**: 填写完整的 API URL（如：`https://api.example.com/v1/chat/completions`）
   - **系统提示词**（可选）: 设置模型的行为

4. **选择图标**
   - 从预设图标中选择
   - 或上传自定义图标（支持 PNG、JPG、SVG 格式）

5. **保存配置**
   - 点击"保存模型"按钮
   - 重启应用后新模型即可使用

#### 配置环境变量

添加模型后，需要在环境变量或前端配置中设置对应的 API Key：

```bash
# 方式 1: 环境变量
export CUSTOM_API_KEY=sk-xxxxx

# 方式 2: 前端配置界面
# 在设置界面输入对应 API Key
```

#### 示例配置

**添加 OpenAI GPT-4**:
```
模型 ID: gpt4
模型名称: GPT-4
API 类型: OpenAI 兼容
模型标识: gpt-4-turbo
API Key 环境变量名: OPENAI_API_KEY
API 基础 URL: https://api.openai.com/v1
系统提示词: You are a helpful assistant.
```

**添加 Anthropic Claude**:
```
模型 ID: claude
模型名称: Claude Opus
API 类型: OpenAI 兼容
模型标识: claude-3-opus-20240229
API Key 环境变量名: ANTHROPIC_API_KEY
API 基础 URL: https://api.anthropic.com/v1
```

**添加通用 LLM**:
```
模型 ID: custom-llm
模型名称: Custom LLM
API 类型: HTTP + SSE
模型标识: custom-model-v1
API Key 环境变量名: CUSTOM_LLM_API_KEY
完整 API URL: https://api.example.com/v1/chat/completions
```
```

### 3. 更新"项目结构"部分

```
```
AI-Chat/
├── .claude/                    # AI 配置与索引
├── docs/                       # 项目文档
│   ├── API_KEY_GUIDE.md        # API Key 申请指南
│   └── MODEL_MANAGER_INTEGRATION.md  # 模型管理集成指南
├── web_chat/                   # Web 应用主目录
│   ├── app.py                  # Flask 应用入口
│   ├── llm_wrapper.py          # LLM 抽象层核心
│   ├── model_manager.py        # 模型管理模块
│   ├── models.json             # 模型配置文件
│   ├── templates/
│   │   ├── index.html          # 前端主页面
│   │   └── model_manager.html  # 模型管理页面
│   └── assets/
│       └── icons/              # 模型图标资源
├── .gitignore                  # Git 忽略规则
├── requirements.txt            # Python 依赖
└── README.md                   # 本文档
```
```

### 4. 更新"核心文件说明"部分

添加新文件说明：

- **`model_manager.py`** - 模型管理模块，提供模型的增删改查功能
- **`models.json`** - 模型配置文件，存储所有模型的定义
- **`templates/model_manager.html`** - 模型管理界面

### 5. 在"常见问题"部分添加新问题

```
### ❓ 如何添加自定义模型？

**答**: 使用模型管理功能添加自定义模型：

1. 访问 `/model_manager` 页面
2. 填写模型配置信息（ID、名称、API 类型等）
3. 根据选择的 API 类型填写相应的参数
4. 选择或上传模型图标
5. 保存配置并重启应用

详细步骤请参考 [模型管理集成指南](docs/MODEL_MANAGER_INTEGRATION.md)。

### ❓ 支持哪些 API 类型？

**答**: 支持以下 4 种 API 类型：

| 类型 | 说明 | 典型应用 |
|------|------|----------|
| OpenAI 兼容 | 使用 OpenAI SDK 格式 | OpenAI GPT、Anthropic Claude、大部分国内模型 |
| Google Gemini | 使用 Google GenAI SDK | Google Gemini 系列 |
| HTTP + SSE | 通用 HTTP 流式接口 | 支持标准 SSE 格式的任何模型 |
| Spark 特殊格式 | 讯飞星火专用格式 | 讯飞星火认知大模型 |

### ❓ 自定义模型的 API Key 如何配置？

**答**: 有两种方式配置 API Key：

1. **环境变量**（推荐用于生产环境）:
   ```bash
   export YOUR_MODEL_API_KEY=sk-xxxxx
   ```

2. **前端配置界面**（适合开发测试）:
   - 在主界面点击设置图标
   - 输入对应环境变量名的 API Key
   - 保存配置
```

---

**说明**: 将上述内容按照对应位置添加到 README.md 文件中。
