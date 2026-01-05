"""pytest 配置和 fixtures

提供测试所需的共享 fixtures 和配置。
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'web_chat'))

# 在导入 app 之前设置测试配置
os.environ['FLASK_TESTING'] = 'True'


@pytest.fixture
def temp_config_file():
    """创建临时配置文件

    Returns:
        tempfile.NamedTemporaryFile: 临时文件对象
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write('{"models": []}')
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_api_keys():
    """示例 API 密钥

    Returns:
        dict: 示例 API 密钥字典
    """
    return {
        'GOOGLE_API_KEY': 'test-google-key',
        'DEEPSEEK_API_KEY': 'test-deepseek-key',
        'MOONSHOT_API_KEY': 'test-moonshot-key',
        'QWEN_API_KEY': 'test-qwen-key',
        'SPARK_API_KEY': 'test-spark-key'
    }


@pytest.fixture
def sample_messages():
    """示例消息列表

    Returns:
        list: 示例消息列表
    """
    return [
        {'role': 'user', 'content': '你好'},
        {'role': 'assistant', 'content': '你好！有什么我可以帮助你的吗？'},
        {'role': 'user', 'content': '介绍一下 Python'}
    ]


@pytest.fixture
def mock_llm_response_stream():
    """模拟 LLM 流式响应

    Yields:
        str: 响应文本片段
    """
    def _generate():
        chunks = ['Python', ' 是', '一种', '编程', '语言', '。']
        for chunk in chunks:
            yield chunk
    return _generate


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """在测试环境中禁用速率限制

    自动应用于所有测试，确保测试不会因为速率限制而失败。
    """
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from web_chat.app import app

    # 在测试配置中标记为测试环境
    app.config['TESTING'] = True


@pytest.fixture
def app_context():
    """Flask 应用上下文"""
    from web_chat.app import app
    with app.app_context():
        with app.test_request_context():
            yield app


@pytest.fixture
def client(app_context):
    """Flask 测试客户端"""
    return app_context.test_client()


@pytest.fixture
def temp_models_file():
    """创建临时模型配置文件

    Returns:
        str: 临时文件路径
    """
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    # 清理
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_dir():
    """创建临时目录

    Returns:
        str: 临时目录路径
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 清理
    import shutil
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def temp_icons_dir():
    """创建临时图标目录

    Returns:
        str: 临时图标目录路径
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 清理
    import shutil
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
