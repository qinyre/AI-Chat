"""LLMWrapper 单元测试

测试 LLMWrapper 类的核心功能，包括：
- 模型配置加载
- 模型列表获取
- SSE 流式响应解析
- 智谱 Token 生成
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from web_chat.llm_wrapper import LLMWrapper, LLMConfig


@pytest.mark.unit
class TestLLMWrapperInit:
    """测试 LLMWrapper 初始化"""

    def test_init_without_params(self):
        """测试无参数初始化"""
        llm = LLMWrapper()
        assert llm.custom_api_keys == {}
        assert isinstance(llm.config, LLMConfig)
        assert llm.config.temperature == 0.7
        assert llm.config.max_tokens == 4096
        assert llm.config.timeout == 30

    def test_init_with_custom_api_keys(self):
        """测试带自定义 API 密钥初始化"""
        custom_keys = {'GOOGLE_API_KEY': 'test-key'}
        llm = LLMWrapper(custom_api_keys=custom_keys)
        assert llm.custom_api_keys == custom_keys

    def test_init_with_custom_config(self):
        """测试带自定义配置初始化"""
        config = LLMConfig(temperature=0.5, max_tokens=2048, timeout=60)
        llm = LLMWrapper(config=config)
        assert llm.config.temperature == 0.5
        assert llm.config.max_tokens == 2048
        assert llm.config.timeout == 60


@pytest.mark.unit
class TestLLMWrapperConfig:
    """测试 LLMWrapper 配置管理"""

    def test_get_default_configs(self, sample_api_keys):
        """测试获取默认配置"""
        llm = LLMWrapper(custom_api_keys=sample_api_keys)
        configs = llm._get_default_configs()

        assert isinstance(configs, dict)
        assert 'google' in configs
        assert 'deepseek' in configs
        assert 'moonshot' in configs
        assert 'qwen' in configs
        assert 'spark' in configs

        # 验证配置结构
        assert configs['google']['type'] == 'google'
        assert configs['deepseek']['type'] == 'openai'
        assert configs['moonshot']['type'] == 'openai'
        assert configs['qwen']['type'] == 'requests_sse'
        assert configs['spark']['type'] == 'spark_requests'

    def test_load_models_from_empty_file(self, temp_config_file):
        """测试从空文件加载模型"""
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write('{"models": []}')

        llm = LLMWrapper()
        with patch('web_chat.llm_wrapper.MODELS_FILE', temp_config_file):
            models = llm._load_models_from_file()

        assert models == {}

    def test_load_models_from_invalid_file(self, temp_config_file):
        """测试从无效文件加载模型"""
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write('invalid json')

        llm = LLMWrapper()
        with patch('web_chat.llm_wrapper.MODELS_FILE', temp_config_file):
            models = llm._load_models_from_file()

        assert models == {}


@pytest.mark.unit
class TestLLMWrapperModels:
    """测试 LLMWrapper 模型管理"""

    def test_get_models(self):
        """测试获取模型列表"""
        llm = LLMWrapper()
        models = llm.get_models()

        assert isinstance(models, list)
        assert 'google' in models
        assert 'deepseek' in models
        assert 'moonshot' in models
        assert 'qwen' in models
        assert 'spark' in models


@pytest.mark.unit
class TestLLMWrapperChat:
    """测试 LLMWrapper 聊天功能"""

    def test_chat_stream_unknown_model(self, sample_messages):
        """测试未知模型 ID"""
        llm = LLMWrapper()
        result = list(llm.chat_stream('unknown_model', sample_messages))

        assert len(result) == 1
        assert result[0] == "Error: Unknown model"

    @patch('web_chat.llm_wrapper.genai.Client')
    def test_chat_stream_google_success(self, mock_client, sample_messages):
        """测试 Google 聊天成功"""
        # 模拟响应
        mock_response = Mock()
        mock_response.text = "Hello!"
        mock_client.return_value.models.generate_content_stream.return_value = [
            mock_response
        ]

        llm = LLMWrapper(custom_api_keys={'GOOGLE_API_KEY': 'test-key'})
        result = list(llm.chat_stream('google', [{'role': 'user', 'content': 'Hi'}]))

        assert result == ["Hello!"]

    @patch('web_chat.llm_wrapper.OpenAI')
    def test_chat_stream_openai_success(self, mock_openai, sample_messages):
        """测试 OpenAI 兼容接口成功"""
        # 模拟响应
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content='Test response'))]
        mock_completion = Mock()
        mock_completion.__iter__ = Mock(return_value=iter([mock_chunk]))

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        llm = LLMWrapper(custom_api_keys={'DEEPSEEK_API_KEY': 'test-key'})
        result = list(llm.chat_stream('deepseek', sample_messages))

        assert result == ["Test response"]


@pytest.mark.unit
class TestSSEParser:
    """测试 SSE 流式响应解析"""

    @pytest.fixture
    def mock_response(self):
        """模拟 HTTP 响应"""
        response = Mock()
        response.iter_lines = Mock(return_value=iter([
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            b'data: {"choices":[{"delta":{"content":" World"}}]}',
            b'data: [DONE]',
            b''
        ]))
        return response

    def test_parse_sse_stream_success(self, mock_response):
        """测试成功解析 SSE 流"""
        llm = LLMWrapper()
        result = list(llm._parse_sse_stream(mock_response))

        assert result == ["Hello", " World"]

    def test_parse_sse_stream_ignore_empty_lines(self, mock_response):
        """测试忽略空行"""
        mock_response.iter_lines = Mock(return_value=iter([
            b'',
            b'data: {"choices":[{"delta":{"content":"Test"}}]}',
            b''
        ]))

        llm = LLMWrapper()
        result = list(llm._parse_sse_stream(mock_response))

        assert result == ["Test"]

    def test_parse_sse_stream_invalid_json(self):
        """测试无效 JSON 处理"""
        mock_response = Mock()
        mock_response.iter_lines = Mock(return_value=iter([
            b'data: invalid json',
            b'data: {"choices":[{"delta":{"content":"Valid"}}]}',
        ]))

        llm = LLMWrapper()
        result = list(llm._parse_sse_stream(mock_response))

        # 应该跳过无效 JSON 并继续处理
        assert result == ["Valid"]


@pytest.mark.unit
class TestZhipuToken:
    """测试智谱 Token 生成"""

    def test_generate_zhipu_token_success(self):
        """测试成功生成 Token"""
        llm = LLMWrapper()
        token = llm._generate_zhipu_token('test_id.test_secret')

        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # header.payload.signature

    def test_generate_zhipu_token_invalid_format(self):
        """测试无效 API Key 格式"""
        llm = LLMWrapper()
        with pytest.raises(ValueError, match='API Key 格式错误'):
            llm._generate_zhipu_token('invalid_key')


@pytest.mark.unit
class TestLLMConfig:
    """测试 LLMConfig 配置类"""

    def test_default_values(self):
        """测试默认值"""
        config = LLMConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.timeout == 30

    def test_custom_values(self):
        """测试自定义值"""
        config = LLMConfig(temperature=0.5, max_tokens=2048, timeout=60)
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.timeout == 60
