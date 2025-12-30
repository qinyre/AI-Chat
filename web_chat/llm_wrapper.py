import os
import json
import requests
from openai import OpenAI
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# 加载环境变量（优先从 .env 文件）
load_dotenv()

# 模型配置文件路径
MODELS_FILE = os.path.join(os.path.dirname(__file__), "models.json")


class LLMWrapper:
    def __init__(self, custom_api_keys=None):
        """
        初始化 LLM 包装器

        Args:
            custom_api_keys: 前端提供的自定义 API 密钥字典
                            格式: {'GOOGLE_API_KEY': 'sk-...', 'DEEPSEEK_API_KEY': 'sk-...'}
        """
        self.custom_api_keys = custom_api_keys or {}
        # 从环境变量读取配置，提供安全的 API 密钥管理
        self.configs = self._load_configs()

    def _get_default_configs(self):
        """
        获取默认内置模型配置
        这些是系统预定义的模型，确保基础功能始终可用
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

    def _load_models_from_file(self):
        """
        从 models.json 加载自定义模型配置
        返回格式: {"model_id": {config_dict}, ...}
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
                elif model["type"] == "google":
                    pass  # Google 只需要 api_key 和 model

                models_config[model_id] = config

            return models_config

        except (json.JSONDecodeError, IOError, KeyError) as e:
            print(f"Failed to load models from file: {e}", flush=True)
            return {}

    def _load_configs(self):
        """
        加载模型配置
        合并默认内置模型和 models.json 中的自定义模型
        """
        # 获取默认内置模型配置
        default_configs = self._get_default_configs()

        # 从文件加载自定义模型配置
        custom_configs = self._load_models_from_file()

        # 合并配置（自定义模型可以覆盖默认模型）
        return {**default_configs, **custom_configs}

    def _get_configs(self):
        """
        获取当前最新的模型配置
        每次调用时重新加载，确保能获取到用户添加的新模型
        """
        return self._load_configs()

    def get_models(self):
        """
        获取可用的模型列表
        每次调用时重新加载配置，确保返回最新的模型列表
        """
        return list(self._get_configs().keys())

    def chat_stream(self, model_id, messages):
        """
        统一的流式对话接口
        messages: list of {"role": "user/assistant/system", "content": "..."}
        """
        print(f"Starting chat stream for {model_id}")
        # 动态获取配置，确保使用最新的模型列表
        config = self._get_configs().get(model_id)
        if not config:
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
            else:
                yield "Error: Unimplemented model type"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"Error: {str(e)}"

    def _chat_google(self, config, messages):
        client = genai.Client(api_key=config["api_key"])
        
        # Convert messages to Google format
        # System prompt is not directly supported in the same way in simple chat usually, 
        # but for simplicity we will just use the chat history.
        
        google_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            # Skip system messages for Google simple mapping or prepend to first user message
            if msg["role"] == "system":
                continue 
            google_contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        # Handle empty history case
        if not google_contents:
            return

        # Use generate_content with stream
        response = client.models.generate_content(
            model=config["model"],
            contents=google_contents,
            # stream=True  # Ensure streaming is supported if enabling
        )
        
        # Note: The original Google.py didn't use stream=True, but for web UI we want streaming.
        # However, the SDK might behave differently. Let's try to simulate streaming or use it if available.
        # Based on docs, client.models.generate_content_stream is likely the method for streaming.
        
        try:
            # Attempt streaming method
            for chunk in client.models.generate_content_stream(
                model=config["model"],
                contents=google_contents
            ):
                if chunk.text:
                    yield chunk.text
        except AttributeError:
             # Fallback to non-streaming if method differs
            response = client.models.generate_content(
                model=config["model"],
                contents=google_contents
            )
            yield response.text

    def _chat_openai(self, config, messages):
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        
        # Inject system prompt if defined in config and not present
        params_messages = list(messages)
        if "system" in config:
            # Check if system is already there? usually web UI sends full history.
            # We will just prepend the system prompt from config if it's not the very first message
            if not params_messages or params_messages[0]["role"] != "system":
                params_messages.insert(0, {"role": "system", "content": config["system"]})
        
        completion = client.chat.completions.create(
            model=config["model"],
            messages=params_messages,
            stream=True,
            temperature=0.7
        )
        
        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def _chat_qwen(self, config, messages):
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config["model"],
            "messages": messages,
            "stream": True,
            "max_tokens": 4096
        }
        
        response = requests.post(config["url"], json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:].strip()
                if data_str == '[DONE]': break
                try:
                    data = json.loads(data_str)
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content
                except:
                    pass

    def _chat_spark(self, config, messages):
        # Spark formatting
        # Original script uses "Bearer " logic
        auth = config["api_key"]
        if not auth.startswith("Bearer "):
            auth = f"Bearer {auth}"
            
        headers = {
            'Authorization': auth,
            'content-type': "application/json"
        }
        
        # Spark in original script only took the LAST message.
        # But we should try to support history if possible. 
        # The original script `spark.py` specifically said: 
        # "Each time deliver only current user message, no history" (line 78).
        # We will respect that behavior for Spark to ensure it works.
        last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
        if not last_user_msg:
            return

        body = {
            "model": config["model"],
            "user": "web_user",
            "messages": [{"role": "user", "content": last_user_msg["content"]}],
            "stream": True
        }
        
        response = requests.post(config["url"], json=body, headers=headers, stream=True)
        
        for line in response.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data_str = line_str[6:].strip()
                if data_str == '[DONE]': break
                try:
                    data = json.loads(data_str)
                    content = data['choices'][0]['delta'].get('content', '')
                    if content:
                        yield content
                except:
                    pass
