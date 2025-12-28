from flask import Flask, render_template, request, Response, stream_with_context, jsonify, send_from_directory
from llm_wrapper import LLMWrapper
import os
import json

app = Flask(__name__)
llm = LLMWrapper()

# API 密钥本地存储文件路径
API_KEYS_FILE = os.path.join(os.path.dirname(__file__), 'api_keys.json')


def load_api_keys_from_file():
    """从本地文件加载 API 密钥配置"""
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f'Failed to load API keys from file: {e}', flush=True)
    return {}


def save_api_keys_to_file(api_keys):
    """保存 API 密钥配置到本地文件"""
    try:
        with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(api_keys, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f'Failed to save API keys to file: {e}', flush=True)
        return False


@app.route('/')
def index():
    return render_template('index.html')


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
def save_config():
    """保存 API 密钥配置"""
    api_keys = request.json
    if save_api_keys_to_file(api_keys):
        return jsonify({'success': True, 'message': '配置已保存'})
    else:
        return jsonify({'success': False, 'message': '保存失败'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    print('Received chat request', flush=True)
    data = request.json
    model_id = data.get('model')
    messages = data.get('messages')
    api_keys = data.get('api_keys', {})
    print(f'Model: {model_id}, Messages: {len(messages)}, API Keys: {len(api_keys)}', flush=True)

    if not model_id or not messages:
        return 'Missing arguments', 400

    def generate():
        llm_with_keys = LLMWrapper(custom_api_keys=api_keys)
        for chunk in llm_with_keys.chat_stream(model_id, messages):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='text/plain')


if __name__ == '__main__':
    print('Starting Web Chat on http://127.0.0.1:5000')
    app.run(debug=True, port=5000)
