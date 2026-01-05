from flask import Flask, render_template, request, Response, stream_with_context, jsonify, send_from_directory
from flask_wtf.csrf import CSRFProtect
from llm_wrapper import LLMWrapper
from model_manager import register_routes
import os
import json
import logging
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

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

# CSRF 保护
csrf = CSRFProtect(app)

# 初始化 LLM Wrapper
llm = LLMWrapper()

# 注册模型管理路由
register_routes(app)

# API 密钥本地存储文件路径
API_KEYS_FILE = os.path.join(os.path.dirname(__file__), 'api_keys.json')


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
    """加载 API 密钥配置"""
    api_keys = load_api_keys_from_file()
    return jsonify(api_keys)


@app.route('/api/config/save', methods=['POST'])
@csrf.exempt  # API 端点使用其他认证方式
def save_config() -> tuple[Response, int] | Response:
    """保存 API 密钥配置

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
    if save_api_keys_to_file(api_keys):
        return jsonify({'success': True, 'message': '配置已保存'})
    else:
        return jsonify({'success': False, 'message': '保存失败'}), 500


@app.route('/api/chat', methods=['POST'])
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
