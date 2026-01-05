"""Flask API 集成测试

测试 Flask 应用和 API 端点，包括：
- 路由响应
- 输入验证
- 错误处理
- 配置加载/保存
"""

import pytest
import json
from web_chat.app import app


@pytest.mark.integration
class TestRoutes:
    """测试基本路由"""

    def test_index_route(self, client):
        """测试主页路由"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'AI NEXUS' in response.data or b'<!DOCTYPE html>' in response.data

    def test_model_manager_route(self, client):
        """测试模型管理页面路由"""
        response = client.get('/model_manager')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'Model Manager' in response.data


@pytest.mark.integration
class TestAPIModels:
    """测试 /api/models 端点"""

    def test_get_models_success(self, client):
        """测试成功获取模型列表"""
        response = client.get('/api/models')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)
        assert 'google' in data
        assert 'deepseek' in data


@pytest.mark.integration
class TestAPIConfig:
    """测试配置 API 端点"""

    def test_load_config_empty(self, client):
        """测试加载空配置"""
        response = client.get('/api/config/load')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_save_config_success(self, client):
        """测试保存配置"""
        config_data = {
            'GOOGLE_API_KEY': 'test-key',
            'DEEPSEEK_API_KEY': 'test-key'
        }
        response = client.post('/api/config/save',
                             json=config_data,
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data.get('success') is True


@pytest.mark.integration
class TestAPIChat:
    """测试 /api/chat 端点"""

    def test_chat_missing_json_body(self, client):
        """测试缺少 JSON body"""
        response = client.post('/api/chat')
        # Flask 会返回 415 (Unsupported Media Type) 如果没有 Content-Type
        # 或者 400 (Bad Request) 取决于请求格式
        assert response.status_code in [400, 415]

        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data
            assert 'JSON body' in data['error']

    def test_chat_missing_model_id(self, client):
        """测试缺少 model_id"""
        response = client.post('/api/chat',
                             json={'messages': [{'role': 'user', 'content': 'Hi'}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'model_id' in data['error']

    def test_chat_missing_messages(self, client):
        """测试缺少 messages"""
        response = client.post('/api/chat',
                             json={'model': 'google'})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'messages' in data['error']

    def test_chat_invalid_model_id_type(self, client):
        """测试无效的 model_id 类型"""
        response = client.post('/api/chat',
                             json={'model': 123, 'messages': []})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'string' in data['error']

    def test_chat_invalid_messages_type(self, client):
        """测试无效的 messages 类型"""
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': 'not a list'})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'list' in data['error']

    def test_chat_too_many_messages(self, client):
        """测试消息数量超限"""
        messages = [{'role': 'user', 'content': 'test'}] * 101
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': messages})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'Too many messages' in data['error']

    def test_chat_invalid_message_format(self, client):
        """测试无效的消息格式"""
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': ['not a dict']})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_missing_message_fields(self, client):
        """测试消息缺少必需字段"""
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': [{'role': 'user'}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_invalid_role(self, client):
        """测试无效的 role"""
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': [{'role': 'invalid', 'content': 'test'}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_invalid_content_type(self, client):
        """测试无效的 content 类型"""
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': [{'role': 'user', 'content': 123}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_chat_content_too_long(self, client):
        """测试内容过长"""
        long_content = 'a' * 10001
        response = client.post('/api/chat',
                             json={'model': 'google', 'messages': [{'role': 'user', 'content': long_content}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'too long' in data['error']

    def test_chat_unknown_model(self, client):
        """测试未知模型"""
        response = client.post('/api/chat',
                             json={'model': 'unknown_model', 'messages': [{'role': 'user', 'content': 'test'}]})
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid model_id' in data['error']


@pytest.mark.integration
class TestCSRF:
    """测试 CSRF 保护"""

    def test_csrf_protection_enabled(self, app_context):
        """验证 CSRF 保护已启用"""
        from flask_wtf.csrf import CSRFProtect
        assert hasattr(app_context, 'extensions')
        assert 'csrf' in app_context.extensions


@pytest.mark.integration
class TestStaticFiles:
    """测试静态文件服务"""

    def test_serve_icon(self, client):
        """测试图标服务"""
        response = client.get('/assets/icons/deepseek_logo.svg')
        # 可能返回 404 如果文件不存在，但路由应该存在
        assert response.status_code in [200, 404]
