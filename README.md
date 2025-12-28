# AI NEXUS

<div align="center">

**多模型 AI 聚合聊天平台**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个统一的 Web 界面，集成多个大型语言模型（LLM）提供商，支持实时流式聊天功能。

[功能特性](#功能特性) • [快速开始](#快速开始) • [配置](#配置) • [技术栈](#技术栈) • [贡献指南](#贡献指南)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [演示截图](#演示截图)
- [快速开始](#快速开始)
- [配置](#配置)
- [使用方法](#使用方法)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

**AI NEXUS** 是一个创新的多模型 AI 聚合聊天平台，旨在为用户提供统一的 Web 界面，无缝集成多个大型语言模型（LLM）提供商。通过实时流式响应和模型特定的对话历史管理，用户可以在单一界面中体验不同 AI 引擎的独特能力。

### 核心价值

- 🔄 **多引擎聚合** - 一站式体验 5 大主流 AI 模型
- ⚡ **实时流式** - 基于 SSE 的流式响应，即时打字机体验
- 💬 **独立对话** - 每个模型维护独立的对话历史
- 🎨 **现代界面** - 玻璃拟态设计，支持深色/浅色主题
- 🔒 **安全配置** - 环境变量管理，保护 API 密钥安全

---

## 功能特性

### 🚀 核心功能

| 功能 | 描述 |
|------|------|
| **多模型支持** | 集成 Google Gemini、DeepSeek、Moonshot/Kimi、Qwen、Spark 五大 AI 模型 |
| **实时流式响应** | 基于 Server-Sent Events (SSE) 的流式传输，提供即时反馈 |
| **独立对话历史** | 每个模型维护独立的对话上下文，支持多轮对话 |
| **Markdown 渲染** | 支持 Markdown 格式的响应内容，包含代码高亮 |
| **主题切换** | 支持深色/浅色主题自由切换 |
| **响应式设计** | 适配桌面端和移动端设备 |

### 🔧 技术特性

- ✅ **统一抽象层** - 通过 `LLMWrapper` 类统一不同 LLM 提供商的 API
- ✅ **环境变量管理** - 使用 `python-dotenv` 安全管理 API 密钥
- ✅ **RESTful API** - 标准的 HTTP 接口设计
- ✅ **流式传输** - Python 生成器 + Flask 流式响应
- ✅ **无框架前端** - 原生 JavaScript，无额外依赖

---

## 演示截图

> 🎨 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 AI NEXUS                              [🌙] [☀️]         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  模型选择：                                                   │
│  [🟢 Gemini] [🔵 DeepSeek] [🟠 Kimi] [🟣 Qwen] [⚡ Spark]  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 对话历史                                                 │ │
│  │                                                          │ │
│  │ 👤 用户: 介绍一下 Python                                  │ │
│  │                                                          │ │
│  │ 🤖 Gemini: Python 是一种高级编程语言...                   │ │
│  │                                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 输入消息...                              [发送]         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- **Python**: 3.11 或更高版本
- **操作系统**: Windows、macOS 或 Linux
- **网络**: 需要访问 LLM 提供商的 API

### 安装步骤

#### 1️⃣ 克隆仓库

```bash
git clone https://github.com/qinyre/AI-Chat.git
cd AI-Chat
```

#### 2️⃣ 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

#### 4️⃣ 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的 API 密钥
notepad .env  # Windows
# 或
nano .env     # macOS / Linux
```

在 `.env` 文件中填入您的 API 密钥：

```bash
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
MOONSHOT_API_KEY=your_moonshot_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
SPARK_API_KEY=your_spark_api_key_here
```

#### 5️⃣ 启动应用

```bash
python web_chat/app.py
```

#### 6️⃣ 访问应用

打开浏览器访问：[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 配置

### API 密钥获取

| 提供商 | 获取地址 | 说明 |
|--------|---------|------|
| **Google Gemini** | [makersuite.google.com](https://makersuite.google.com/app/apikey) | 免费 API 密钥 |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com/api_keys) | 需注册账号 |
| **Moonshot / Kimi** | [platform.moonshot.cn](https://platform.moonshot.cn/console/api-keys) | 需注册账号 |
| **Qwen (通义千问)** | [siliconflow.cn](https://siliconflow.cn/account/ak) | 需注册账号 |
| **Spark (讯飞星火)** | [xfyun.cn](https://console.xfyun.cn/services/cbm) | 需注册账号 |

### 环境变量说明

完整的配置选项请参考 [`.env.example`](.env.example) 文件。

```bash
# Google Gemini
GOOGLE_API_KEY=your_api_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Moonshot / Kimi
MOONSHOT_API_KEY=your_api_key_here
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

# Qwen (通义千问)
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://api.siliconflow.cn/v1/chat/completions

# Spark (讯飞星火)
SPARK_API_KEY=your_api_key_here
SPARK_BASE_URL=https://spark-api-open.xf-yun.com/v2/chat/completions
```

---

## 使用方法

### 基本使用

1. **选择模型** - 点击顶部模型图标切换不同的 AI 模型
2. **输入消息** - 在底部输入框输入您的问题
3. **发送请求** - 点击"发送"按钮或按 Enter 键
4. **查看响应** - AI 的回复会以流式方式逐字显示

### 高级功能

#### 切换主题

点击右上角的主题图标切换深色/浅色模式：
- 🌙 深色模式
- ☀️ 浅色模式

#### 多轮对话

每个模型维护独立的对话历史，支持上下文理解：

```
用户: 什么是 Python？
AI: Python 是一种编程语言...
用户: 它有哪些特点？
AI: Python 的主要特点包括...（基于上一轮对话的上下文）
```

> **注意**: Spark 模型不支持对话历史，每次仅响应当前消息。

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11+ | 主要编程语言 |
| **Flask** | 3.0+ | Web 框架 |
| **requests** | 2.31+ | HTTP 请求库 |
| **OpenAI SDK** | 1.0+ | DeepSeek、Moonshot 集成 |
| **Google GenAI** | 0.3+ | Gemini 集成 |
| **python-dotenv** | 1.0+ | 环境变量管理 |

### 前端

| 技术 | 用途 |
|------|------|
| **原生 JavaScript** | 交互逻辑 |
| **TailwindCSS** | 样式框架（CDN） |
| **Marked.js** | Markdown 渲染 |

### LLM 提供商

| 提供商 | 模型 | SDK/协议 |
|--------|------|----------|
| Google | Gemini 2.5 Flash | google-genai SDK |
| DeepSeek | deepseek-chat | OpenAI SDK |
| Moonshot | Kimi k2-turbo-preview | OpenAI SDK |
| Qwen | Qwen2.5-VL-72B | HTTP + SSE |
| Spark | Spark x1 | HTTP + SSE |

---

## 项目结构

```
AI-Chat/
├── .claude/                    # AI 配置与索引
├── web_chat/                   # Web 应用主目录
│   ├── app.py                  # Flask 应用入口
│   ├── llm_wrapper.py          # LLM 抽象层核心
│   ├── templates/
│   │   └── index.html          # 前端单页应用
│   ├── assets/
│   │   └── icons/              # 模型图标资源
│   └── CLAUDE.md               # 模块文档
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
├── requirements.txt            # Python 依赖
├── CLAUDE.md                   # 根级 AI 上下文文档
└── README.md                   # 本文档
```

### 核心文件说明

- **`app.py`** - Flask 应用入口，定义路由和启动配置
- **`llm_wrapper.py`** - LLM 抽象层，统一不同提供商的 API
- **`templates/index.html`** - 前端单页应用，包含所有 UI 和交互逻辑

---

## 开发指南

### 添加新的 LLM 提供商

1. **在 `.env.example` 中添加配置**：
   ```bash
   NEW_PROVIDER_API_KEY=your_api_key_here
   NEW_PROVIDER_BASE_URL=https://api.example.com/v1
   ```

2. **在 `llm_wrapper.py` 中添加模型配置**：
   ```python
   "new_provider": {
       "type": "new_type",
       "api_key": os.environ.get("NEW_PROVIDER_API_KEY", ""),
       "base_url": os.environ.get("NEW_PROVIDER_BASE_URL", "https://api.example.com/v1"),
       "model": "model-name"
   }
   ```

3. **实现 `_chat_provider()` 方法**：
   ```python
   def _chat_new_provider(self, config, messages):
       # 实现流式聊天逻辑
       for chunk in ...:
           yield chunk
   ```

4. **在 `chat_stream()` 中添加路由**：
   ```python
   elif config["type"] == "new_type":
       yield from self._chat_new_provider(config, messages)
   ```

5. **在前端 `index.html` 中添加图标映射**：
   ```javascript
   const modelIcons = {
       'new_provider': {
           src: '/assets/icons/new_provider_logo.svg',
           class: 'new-provider'
       }
   };
   ```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-flask pytest-cov

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=web_chat --cov-report=html
```

---

## 常见问题

### ❓ 启动时提示缺少环境变量怎么办？

**答**: 确保：
1. 已创建 `.env` 文件（从 `.env.example` 复制）
2. `.env` 文件中填入了有效的 API 密钥
3. `.env` 文件位于项目根目录

### ❓ 为什么 Spark 模型没有对话历史？

**答**: Spark API 的限制导致它不支持上下文记忆。每次请求仅发送当前用户消息，不传递历史记录。这是 Spark API 的设计限制，不是项目的问题。

### ❓ 流式响应中断怎么办？

**答**:
1. 检查网络连接稳定性
2. 确认 API 密钥是否有效
3. 检查 API 速率限制（每个提供商都有速率限制）
4. 查看浏览器控制台是否有错误信息

### ❓ 如何自定义系统提示词？

**答**: 在 `llm_wrapper.py` 的模型配置中添加 `system` 字段：

```python
"deepseek": {
    "type": "openai",
    "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
    "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    "model": "deepseek-chat",
    "system": "You are a helpful assistant"  # 自定义系统提示词
}
```

> **注意**: 仅 OpenAI 兼容的提供商（DeepSeek、Moonshot）支持系统提示词。

### ❓ API 密钥安全吗？

**答**: 项目采用最佳实践：
- ✅ 使用环境变量存储 API 密钥
- ✅ `.env` 文件已被 `.gitignore` 忽略
- ✅ 提供 `.env.example` 作为配置模板
- ✅ 永远不要将 `.env` 文件提交到 Git 仓库

---

## 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

1. 🐛 **报告问题** - 在 Issues 中报告 Bug
2. 💡 **功能建议** - 提出新功能或改进建议
3. 🔧 **提交代码** - 提交 Pull Request
4. 📖 **改进文档** - 完善项目文档

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- **Python**: 遵循 [PEP 8](https://pep8.org/) 风格指南
- **JavaScript**: 使用 ES6+ 语法
- **注释**: 关键代码需要添加注释说明
- **提交信息**: 使用清晰的提交消息

---

## 许可证

本项目采用 [MIT](LICENSE) 许可证。

```
MIT License

Copyright (c) 2024 AI NEXUS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 致谢

感谢以下开源项目和服务：

- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
- [OpenAI Python SDK](https://github.com/openai/openai-python) - OpenAI API 客户端
- [Google GenAI SDK](https://github.com/googleapis/python-genai) - Google Gemini SDK
- [TailwindCSS](https://tailwindcss.com/) - CSS 框架
- [Marked.js](https://marked.js.org/) - Markdown 解析器

---

## 联系方式

- **项目主页**: [https://github.com/qinyre/AI-Chat](https://github.com/qinyre/AI-Chat)
- **问题反馈**: [GitHub Issues](https://github.com/qinyre/AI-Chat/issues)
- **邮箱**: qinyre801014@gmail.com

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by AI NEXUS Team

</div>
