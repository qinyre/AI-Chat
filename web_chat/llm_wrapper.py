"""LLM Wrapper - 统一的 LLM API 抽象层

此模块提供了统一的接口来调用多个 LLM 提供商的 API，包括：
- Google Gemini
- OpenAI 兼容接口（DeepSeek, Moonshot, 智谱 GLM）
- HTTP SSE 接口（Qwen, Spark）
"""

import os
import json
import requests
import time
import hmac
import hashlib
import base64
import logging
from typing import Dict, List, Optional, Generator, Any, Union
from dataclasses import dataclass

from openai import OpenAI
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# 加载环境变量（优先从 .env 文件）
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 模型配置文件路径
MODELS_FILE = os.path.join(os.path.dirname(__file__), "models.json")


@dataclass
class LLMConfig:
    """LLM 配置类

    Attributes:
        temperature: 生成温度，控制随机性 (0.0-1.0)
        max_tokens: 最大生成令牌数
        timeout: 请求超时时间（秒）
    """
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 30


class LLMWrapper:
    """LLM API 统一包装器

    提供统一的接口来调用多个 LLM 提供商的 API，支持流式响应。

    Example:
        >>> llm = LLMWrapper(custom_api_keys={'OPENAI_API_KEY': 'sk-...'})
        >>> for chunk in llm.chat_stream('deepseek', messages):
        ...     print(chunk, end='', flush=True)
    """

    def __init__(
        self,
        custom_api_keys: Optional[Dict[str, str]] = None,
        config: Optional[LLMConfig] = None
    ) -> None:
        """初始化 LLM 包装器

        Args:
            custom_api_keys: 前端提供的自定义 API 密钥字典
                格式: {'GOOGLE_API_KEY': 'sk-...', 'DEEPSEEK_API_KEY': 'sk-...'}
            config: LLM 配置对象，如果为 None 则使用默认配置
        """
        self.custom_api_keys = custom_api_keys or {}
        self.config = config or LLMConfig()
        # 从环境变量读取配置，提供安全的 API 密钥管理
        self.configs = self._load_configs()

    def _get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取默认内置模型配置

        这些是系统预定义的模型，确保基础功能始终可用。

        Returns:
            Dict[str, Dict[str, Any]]: 默认模型配置字典
        """
        return {
            "google": {
                "type": "google",
                "api_key": self.custom_api_keys.get('GOOGLE_API_KEY') or os.environ.get("GOOGLE_API_KEY", ""),
                "model": "gemini-2.5-flash"
            },
            "deepseek": {
                "type": "openai",
                "api_key": self.custom_api_keys.get('DEEPSEEK_API_KEY') or os.environ.get("DEEPSEEK_API_KEY", ""),
                "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "model": "deepseek-chat",
                "system": "You are a helpful assistant"
            },
            "moonshot": {
                "type": "openai",
                "api_key": self.custom_api_keys.get('MOONSHOT_API_KEY') or os.environ.get("MOONSHOT_API_KEY", ""),
                "base_url": os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1"),
                "model": "kimi-k2-turbo-preview",
                "system": "你是一只猫娘，你每回答一次问题都会在最后面加一个：,喵~"
            },
            "qwen": {
                "type": "requests_sse",
                "url": os.environ.get("QWEN_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions"),
                "api_key": self.custom_api_keys.get('QWEN_API_KEY') or os.environ.get("QWEN_API_KEY", ""),
                "model": "Qwen/Qwen2.5-VL-72B-Instruct"
            },
            "spark": {
                "type": "spark_requests",
                "url": os.environ.get("SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/v2/chat/completions"),
                "api_key": self.custom_api_keys.get('SPARK_API_KEY') or os.environ.get("SPARK_API_KEY", ""),
                "model": "x1"
            }
        }

    def _load_models_from_file(self) -> Dict[str, Dict[str, Any]]:
        """从 models.json 加载自定义模型配置

        Returns:
            Dict[str, Dict[str, Any]]: 自定义模型配置字典，格式为 {"model_id": {config_dict}, ...}
        """
        if not os.path.exists(MODELS_FILE):
            return {}

        try:
            with open(MODELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            models_config = {}
            for model in data.get("models", []):
                if not model.get("enabled", True):
                    continue

                model_id = model["id"]
                api_key_name = model.get("api_key_name", "")
                config = {
                    "type": model["type"],
                    "model": model["model"],
                    "api_key": self.custom_api_keys.get(api_key_name) or os.environ.get(api_key_name, "")
                }

                # 根据类型添加可选字段
                if model["type"] == "openai":
                    if "base_url" in model:
                        config["base_url"] = model["base_url"]
                    if "system" in model:
                        config["system"] = model["system"]
                elif model["type"] in ["requests_sse", "spark_requests"]:
                    if "url" in model:
                        config["url"] = model["url"]
                elif model["type"] == "zhipu":
                    if "base_url" in model:
                        config["base_url"] = model["base_url"]
                    if "system" in model:
                        config["system"] = model["system"]
                elif model["type"] == "google":
                    pass  # Google 只需要 api_key 和 model

                models_config[model_id] = config

            return models_config

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"Failed to load models from file: {e}")
            return {}

    def _load_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载模型配置

        合并默认内置模型和 models.json 中的自定义模型。

        Returns:
            Dict[str, Dict[str, Any]]: 完整的模型配置字典
        """
        # 获取默认内置模型配置
        default_configs = self._get_default_configs()

        # 从文件加载自定义模型配置
        custom_configs = self._load_models_from_file()

        # 合并配置（自定义模型可以覆盖默认模型）
        return {**default_configs, **custom_configs}

    def _get_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取当前最新的模型配置

        每次调用时重新加载，确保能获取到用户添加的新模型。

        Returns:
            Dict[str, Dict[str, Any]]: 最新的模型配置字典
        """
        return self._load_configs()

    def get_models(self) -> List[str]:
        """获取可用的模型列表

        每次调用时重新加载配置，确保返回最新的模型列表。

        Returns:
            List[str]: 可用模型 ID 列表
        """
        return list(self._get_configs().keys())

    def chat_stream(
        self,
        model_id: str,
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """统一的流式对话接口

        Args:
            model_id: 模型 ID
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}, ...]

        Yields:
            str: 流式响应的文本片段

        Example:
            >>> messages = [{"role": "user", "content": "你好"}]
            >>> for chunk in llm.chat_stream('deepseek', messages):
            ...     print(chunk, end='', flush=True)
        """
        logger.info(f"Starting chat stream for {model_id}")
        # 动态获取配置，确保使用最新的模型列表
        config = self._get_configs().get(model_id)
        if not config:
            logger.error(f"Unknown model: {model_id}")
            yield "Error: Unknown model"
            return

        try:
            if config["type"] == "google":
                yield from self._chat_google(config, messages)
            elif config["type"] == "openai":
                yield from self._chat_openai(config, messages)
            elif config["type"] == "requests_sse":
                yield from self._chat_qwen(config, messages)
            elif config["type"] == "spark_requests":
                yield from self._chat_spark(config, messages)
            elif config["type"] == "zhipu":
                yield from self._chat_zhipu(config, messages)
            else:
                logger.error(f"Unimplemented model type: {config['type']}")
                yield "Error: Unimplemented model type"
        except Exception as e:
            logger.exception(f"Error during chat stream for {model_id}")
            yield f"Error: {str(e)}"

    def _parse_sse_stream(self, response: requests.Response) -> Generator[str, None, None]:
        """通用的 SSE 流式响应解析器

        解析 Server-Sent Events 格式的流式响应。

        Args:
            response: requests.Response 对象

        Yields:
            str: 解析出的文本内容
        """
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:].strip()
                if data_str == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.debug(f"Failed to parse SSE chunk: {e}")
                    continue

    def _chat_google(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Google Gemini 聊天方法

        Args:
            config: 模型配置字典
            messages: 消息列表

        Yields:
            str: 响应文本片段
        """
        client = genai.Client(api_key=config["api_key"])

        # 转换消息为 Google 格式
        google_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            # 跳过系统消息（Google 简单映射不直接支持）
            if msg["role"] == "system":
                continue
            google_contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        # 处理空历史情况
        if not google_contents:
            logger.warning("No valid messages for Google API")
            return

        # 使用流式生成
        try:
            for chunk in client.models.generate_content_stream(
                model=config["model"],
                contents=google_contents
            ):
                if chunk.text:
                    yield chunk.text
        except AttributeError:
            # 回退到非流式（如果方法不同）
            logger.info("Falling back to non-streaming for Google API")
            response = client.models.generate_content(
                model=config["model"],
                contents=google_contents
            )
            yield response.text

    def _chat_openai(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """OpenAI 兼容接口聊天方法（DeepSeek, Moonshot 等）

        Args:
            config: 模型配置字典
            messages: 消息列表

        Yields:
            str: 响应文本片段
        """
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])

        # 注入系统提示词（如果在配置中定义且消息中不存在）
        params_messages = list(messages)
        if "system" in config:
            if not params_messages or params_messages[0]["role"] != "system":
                params_messages.insert(0, {"role": "system", "content": config["system"]})

        completion = client.chat.completions.create(
            model=config["model"],
            messages=params_messages,
            stream=True,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def _chat_qwen(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Qwen 聊天方法（HTTP + SSE）

        Args:
            config: 模型配置字典
            messages: 消息列表

        Yields:
            str: 响应文本片段
        """
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config["model"],
            "messages": messages,
            "stream": True,
            "max_tokens": self.config.max_tokens
        }

        response = requests.post(
            config["url"],
            json=payload,
            headers=headers,
            stream=True,
            timeout=self.config.timeout
        )
        response.raise_for_status()

        yield from self._parse_sse_stream(response)

    def _chat_spark(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Spark 聊天方法（HTTP + SSE）

        注意：Spark API 不支持对话历史，每次只发送最后一条用户消息。

        Args:
            config: 模型配置字典
            messages: 消息列表

        Yields:
            str: 响应文本片段
        """
        # Spark 格式化
        auth = config["api_key"]
        if not auth.startswith("Bearer "):
            auth = f"Bearer {auth}"

        headers = {
            'Authorization': auth,
            'content-type': "application/json"
        }

        # Spark 原始脚本只使用最后一条消息
        # 我们尊重这个行为以确保 Spark 正常工作
        last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
        if not last_user_msg:
            logger.warning("No user message found for Spark API")
            return

        body = {
            "model": config["model"],
            "user": "web_user",
            "messages": [{"role": "user", "content": last_user_msg["content"]}],
            "stream": True
        }

        response = requests.post(
            config["url"],
            json=body,
            headers=headers,
            stream=True,
            timeout=self.config.timeout
        )

        yield from self._parse_sse_stream(response)

    def _generate_zhipu_token(self, api_key: str) -> str:
        """生成智谱 AI 的 JWT Token

        Args:
            api_key: API 密钥，格式为 id.secret

        Returns:
            str: JWT Token 字符串

        Raises:
            ValueError: 如果 API Key 格式错误
        """
        try:
            id, secret = api_key.split('.')
        except ValueError:
            raise ValueError("智谱 API Key 格式错误，应为 id.secret")

        # Token 有效期：1小时
        exp = int(time.time()) + 3600

        header = {
            "alg": "HS256",
            "sign_type": "SIGN"
        }

        payload = {
            "api_key": id,
            "exp": exp,
            "timestamp": int(time.time())
        }

        # 编码 header
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).decode().rstrip('=')

        # 编码 payload
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(',', ':')).encode()
        ).decode().rstrip('=')

        # 生成签名
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()

        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

        return f"{message}.{signature_b64}"

    def _chat_zhipu(
        self,
        config: Dict[str, Any],
        messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """智谱 AI (GLM) 聊天方法（使用 JWT Token 认证）

        Args:
            config: 模型配置字典
            messages: 消息列表

        Yields:
            str: 响应文本片段
        """
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/paas/v4")

        # 生成 JWT Token
        token = self._generate_zhipu_token(config["api_key"])

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 注入系统提示词
        params_messages = list(messages)
        if "system" in config:
            if not params_messages or params_messages[0]["role"] != "system":
                params_messages.insert(0, {"role": "system", "content": config["system"]})

        payload = {
            "model": config["model"],
            "messages": params_messages,
            "stream": True
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
            stream=True,
            timeout=self.config.timeout
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Zhipu API HTTP error: {e}")
            yield f"Error: HTTP {e.response.status_code} - {e.response.text}"
            return

        yield from self._parse_sse_stream(response)
