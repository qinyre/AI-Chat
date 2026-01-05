from flask import Flask, render_template, request, Response, stream_with_context, jsonify, send_from_directory
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from llm_wrapper import LLMWrapper
from model_manager import register_routes
import os
import json
import logging
import threading
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Tuple

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_chat.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-use-openssl-rand-hex-32')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# 检查是否在测试环境中
app.config['TESTING'] = os.environ.get('FLASK_TESTING') == 'True'

# CSRF 保护
csrf = CSRFProtect(app)

# 速率限制（在测试环境中禁用）
if app.config.get('TESTING'):
    # 测试环境：使用极高的限制值，实际上禁用速率限制
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["10000 per day", "10000 per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
else:
    # 生产环境：正常速率限制
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
        strategy="fixed-window"
    )

# 初始化 LLM Wrapper
llm = LLMWrapper()

# 注册模型管理路由（传入 limiter 以启用速率限制）
register_routes(app, limiter)

# 速率限制辅助函数（根据环境调整限制）
def rate_limit(limit_string: str):
    """根据环境返回速率限制装饰器

    Args:
        limit_string: 限制字符串，如 "10 per minute"

    Returns:
        装饰器函数
    """
    if app.config.get('TESTING'):
        # 测试环境：使用极高的限制
        return limiter.limit("10000 per minute")
    else:
        # 生产环境：使用指定的限制
        return limiter.limit(limit_string)

# API 密钥本地存储文件路径
API_KEYS_FILE = os.path.join(os.path.dirname(__file__), 'api_keys.json')


class ConfigCache:
    """配置缓存管理类

    提供线程安全的配置缓存，支持自动失效机制。
    通过检查文件修改时间来判断缓存是否有效。

    Attributes:
        _cache: 缓存的配置数据
        _mtime: 文件修改时间
        _lock: 线程锁，确保线程安全
    """

    def __init__(self) -> None:
        """初始化配置缓存"""
        self._cache: Dict[str, str] = {}
        self._mtime: float = 0
        self._lock = threading.Lock()

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效

        通过比较文件修改时间来判断缓存是否过期。

        Returns:
            bool: 缓存有效返回 True，否则返回 False
        """
        if not os.path.exists(API_KEYS_FILE):
            return False

        current_mtime = os.path.getmtime(API_KEYS_FILE)
        return current_mtime == self._mtime

    def get(self, force_reload: bool = False) -> Dict[str, str]:
        """获取配置（带缓存）

        Args:
            force_reload: 是否强制重新加载，忽略缓存

        Returns:
            Dict[str, str]: API 密钥字典
        """
        with self._lock:
            # 如果缓存有效且不强制重新加载，直接返回缓存
            if not force_reload and self._is_cache_valid() and self._cache:
                return self._cache.copy()

            # 缓存失效或强制重新加载，从文件加载
            if os.path.exists(API_KEYS_FILE):
                try:
                    with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                        self._cache = json.load(f)
                        self._mtime = os.path.getmtime(API_KEYS_FILE)
                        logger.debug(f'API keys loaded from file (cache updated)')
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f'Failed to load API keys from file: {e}')
                    self._cache = {}
                    self._mtime = 0
            else:
                self._cache = {}
                self._mtime = 0

            return self._cache.copy()

    def set(self, api_keys: Dict[str, str]) -> bool:
        """设置配置并保存到文件

        Args:
            api_keys: API 密钥字典

        Returns:
            bool: 保存是否成功
        """
        with self._lock:
            try:
                with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(api_keys, f, indent=2, ensure_ascii=False)
                # 更新缓存和修改时间
                self._cache = api_keys.copy()
                self._mtime = os.path.getmtime(API_KEYS_FILE)
                logger.info('API keys saved successfully (cache updated)')
                return True
            except IOError as e:
                logger.error(f'Failed to save API keys to file: {e}')
                return False

    def invalidate(self) -> None:
        """使缓存失效

        下次调用 get() 时会重新从文件加载配置。
        """
        with self._lock:
            self._cache = {}
            self._mtime = 0
            logger.debug('Config cache invalidated')


# 创建全局配置缓存实例
config_cache = ConfigCache()


def load_api_keys_from_file() -> Dict[str, str]:
    """从本地文件加载 API 密钥配置

    Returns:
        Dict[str, str]: API 密钥字典
    """
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f'Failed to load API keys from file: {e}')
    return {}


def save_api_keys_to_file(api_keys: Dict[str, str]) -> bool:
    """保存 API 密钥配置到本地文件

    Args:
        api_keys: API 密钥字典

    Returns:
        bool: 保存是否成功
    """
    try:
        with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(api_keys, f, indent=2, ensure_ascii=False)
        logger.info('API keys saved successfully')
        return True
    except IOError as e:
        logger.error(f'Failed to save API keys to file: {e}')
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/model_manager')
def model_manager_page():
    """模型管理页面"""
    return render_template('model_manager.html')


@app.route('/assets/icons/<filename>')
def serve_icon(filename):
    """Serve local icon files from assets/icons/"""
    icons_dir = os.path.join(os.path.dirname(__file__), 'assets', 'icons')
    return send_from_directory(icons_dir, filename)


@app.route('/api/models')
def get_models():
    return jsonify(llm.get_models())


@app.route('/api/config/load', methods=['GET'])
def load_config():
    """加载 API 密钥配置（使用缓存）"""
    api_keys = config_cache.get()
    return jsonify(api_keys)


@app.route('/api/config/save', methods=['POST'])
@rate_limit("5 per minute")  # 速率限制：每分钟最多 5 次请求
@csrf.exempt  # API 端点使用其他认证方式
def save_config() -> tuple[Response, int] | Response:
    """保存 API 密钥配置（使用缓存）

    POST 请求格式:
    {
        "GOOGLE_API_KEY": "sk-...",
        "DEEPSEEK_API_KEY": "sk-...",
        ...
    }

    Returns:
        Response: 成功或失败消息
    """
    if not request.json:
        logger.warning('Invalid request: missing JSON body')
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    api_keys = request.json
    if config_cache.set(api_keys):
        return jsonify({'success': True, 'message': '配置已保存'})
    else:
        return jsonify({'success': False, 'message': '保存失败'}), 500


@app.route('/api/chat', methods=['POST'])
@rate_limit("10 per minute")  # 速率限制：每分钟最多 10 次请求
@csrf.exempt  # API 端点使用其他认证方式（API Key）
def chat() -> tuple[Response, int] | Response:
    """流式聊天端点

    POST 请求格式:
    {
        "model": str,           # 模型 ID
        "messages": List[Dict], # 消息列表
        "api_keys": Dict        # API 密钥（可选）
    }

    Returns:
        Response: 流式响应或错误信息
    """
    logger.info('Received chat request')

    # 获取请求数据
    if not request.json:
        logger.warning('Invalid request: missing JSON body')
        return jsonify({'error': 'Invalid request: missing JSON body'}), 400

    data = request.json
    model_id = data.get('model')
    messages = data.get('messages')
    api_keys = data.get('api_keys', {})

    # 输入验证
    if not model_id:
        logger.warning('Invalid request: missing model_id')
        return jsonify({'error': 'Missing model_id'}), 400

    if not isinstance(model_id, str):
        logger.warning(f'Invalid request: model_id must be string, got {type(model_id)}')
        return jsonify({'error': 'model_id must be a string'}), 400

    if not messages:
        logger.warning('Invalid request: missing messages')
        return jsonify({'error': 'Missing messages'}), 400

    if not isinstance(messages, list):
        logger.warning(f'Invalid request: messages must be list, got {type(messages)}')
        return jsonify({'error': 'messages must be a list'}), 400

    if len(messages) > 100:
        logger.warning(f'Invalid request: too many messages ({len(messages)} > 100)')
        return jsonify({'error': 'Too many messages (max 100)'}), 400

    # 验证消息格式
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            logger.warning(f'Invalid message at index {i}: not a dict')
            return jsonify({'error': f'Message at index {i} must be a dict'}), 400

        if 'role' not in msg or 'content' not in msg:
            logger.warning(f'Invalid message at index {i}: missing role or content')
            return jsonify({'error': f'Message at index {i} missing role or content'}), 400

        if msg['role'] not in ['user', 'assistant', 'system']:
            logger.warning(f'Invalid message at index {i}: invalid role {msg["role"]}')
            return jsonify({'error': f'Invalid role at index {i}: {msg["role"]}'}), 400

        if not isinstance(msg['content'], str):
            logger.warning(f'Invalid message at index {i}: content not a string')
            return jsonify({'error': f'Message content at index {i} must be a string'}), 400

        if len(msg['content']) > 10000:
            logger.warning(f'Invalid message at index {i}: content too long ({len(msg["content"])} > 10000)')
            return jsonify({'error': f'Message at index {i} too long (max 10000 characters)'}), 400

    # 验证模型是否存在
    available_models = llm.get_models()
    if model_id not in available_models:
        logger.warning(f'Invalid request: model_id {model_id} not found')
        return jsonify({'error': f'Invalid model_id: {model_id}'}), 400

    logger.info(f'Chat request validated: Model={model_id}, Messages={len(messages)}')

    def generate():
        """生成流式响应"""
        llm_with_keys = LLMWrapper(custom_api_keys=api_keys)
        try:
            for chunk in llm_with_keys.chat_stream(model_id, messages):
                yield chunk
        except Exception as e:
            logger.error(f'Error during chat stream: {e}')
            yield f'\n\n[错误: {str(e)}]'

    return Response(stream_with_context(generate()), mimetype='text/plain')


if __name__ == '__main__':
    # 从环境变量读取配置
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']

    logger.info(f'Starting Web Chat on http://{host}:{port}')
    logger.info(f'Debug mode: {debug_mode}')

    app.run(host=host, port=port, debug=debug_mode)
