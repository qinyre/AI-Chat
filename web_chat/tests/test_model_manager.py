"""Model Manager 单元测试和集成测试

测试 model_manager 模块的核心功能，包括：
- 模型配置加载和保存
- 模型增删改查
- 图标上传
- 文件验证
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from web_chat import model_manager


@pytest.mark.unit
class TestLoadModels:
    """测试 load_models 函数"""

    def test_load_models_from_existing_file(self, temp_models_file):
        """测试从现有文件加载模型"""
        # 创建临时测试文件
        test_data = {
            "version": "1.0.0",
            "models": [
                {"id": "test-model", "name": "Test Model"}
            ],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        # 临时替换 MODELS_FILE
        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            result = model_manager.load_models()
            assert result == test_data
            assert result["version"] == "1.0.0"
            assert len(result["models"]) == 1
        finally:
            model_manager.MODELS_FILE = original_file

    def test_load_models_from_example_file(self, temp_dir):
        """测试从 example 文件初始化"""
        # 创建 example 文件
        example_file = os.path.join(temp_dir, "models.json.example")
        models_file = os.path.join(temp_dir, "models.json")

        example_data = {
            "version": "1.0.0",
            "models": [],
            "api_types": {}
        }
        with open(example_file, 'w', encoding='utf-8') as f:
            json.dump(example_data, f)

        # 临时替换文件路径
        original_models_file = model_manager.MODELS_FILE
        original_example_file = model_manager.MODELS_EXAMPLE_FILE

        model_manager.MODELS_FILE = models_file
        model_manager.MODELS_EXAMPLE_FILE = example_file

        try:
            result = model_manager.load_models()
            assert result == example_data
            assert os.path.exists(models_file)
        finally:
            model_manager.MODELS_FILE = original_models_file
            model_manager.MODELS_EXAMPLE_FILE = original_example_file

    def test_load_models_invalid_json(self, temp_models_file):
        """测试加载无效 JSON"""
        # 写入无效 JSON
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            result = model_manager.load_models()
            # 应该返回默认空配置
            assert result["version"] == "1.0.0"
            assert result["models"] == []
            assert result["api_types"] == {}
        finally:
            model_manager.MODELS_FILE = original_file

    def test_load_models_no_files(self, temp_dir):
        """测试没有任何配置文件的情况"""
        models_file = os.path.join(temp_dir, "nonexistent.json")
        example_file = os.path.join(temp_dir, "nonexistent.example.json")

        original_models_file = model_manager.MODELS_FILE
        original_example_file = model_manager.MODELS_EXAMPLE_FILE

        model_manager.MODELS_FILE = models_file
        model_manager.MODELS_EXAMPLE_FILE = example_file

        try:
            result = model_manager.load_models()
            assert result["version"] == "1.0.0"
            assert result["models"] == []
            assert result["api_types"] == {}
        finally:
            model_manager.MODELS_FILE = original_models_file
            model_manager.MODELS_EXAMPLE_FILE = original_example_file


@pytest.mark.unit
class TestSaveModels:
    """测试 save_models 函数"""

    def test_save_models_success(self, temp_models_file):
        """测试成功保存模型配置"""
        test_data = {
            "version": "1.0.0",
            "models": [{"id": "test"}],
            "api_types": {}
        }

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            result = model_manager.save_models(test_data)
            assert result is True

            # 验证文件内容
            with open(temp_models_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            assert saved_data == test_data
        finally:
            model_manager.MODELS_FILE = original_file

    def test_save_models_io_error(self):
        """测试保存时发生 IO 错误"""
        # 使用无效路径
        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = "/invalid/path/models.json"

        try:
            result = model_manager.save_models({"test": "data"})
            assert result is False
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.unit
class TestAllowedFile:
    """测试 allowed_file 函数"""

    def test_allowed_file_valid_extensions(self):
        """测试有效的文件扩展名"""
        valid_files = [
            "test.png",
            "photo.jpg",
            "image.jpeg",
            "icon.svg",
            "animation.gif",
            "TEST.PNG"  # 测试大小写
        ]
        for filename in valid_files:
            assert model_manager.allowed_file(filename) is True

    def test_allowed_file_invalid_extensions(self):
        """测试无效的文件扩展名"""
        invalid_files = [
            "test.exe",
            "script.js",
            "document.pdf",
            "archive.zip",
            "no_extension",
            "hidden.file",
            ""
        ]
        for filename in invalid_files:
            assert model_manager.allowed_file(filename) is False


@pytest.mark.integration
class TestGetAllModels:
    """测试 get_all_models 函数"""

    def test_get_all_models_success(self, temp_models_file, app_context):
        """测试成功获取所有模型"""
        test_data = {
            "version": "1.0.0",
            "models": [
                {"id": "google", "name": "Google Gemini"},
                {"id": "deepseek", "name": "DeepSeek"}
            ],
            "api_types": {
                "google": {"name": "Google"},
                "openai": {"name": "OpenAI"}
            }
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            with app_context.app_context():
                response = model_manager.get_all_models()
                data = response.get_json()
                assert data["success"] is True
                assert len(data["models"]) == 2
                assert len(data["api_types"]) == 2
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.integration
class TestAddModel:
    """测试 add_model 函数"""

    def test_add_model_success(self, temp_models_file, app_context):
        """测试成功添加模型"""
        # 初始化测试数据
        initial_data = {
            "version": "1.0.0",
            "models": [],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        # 模拟请求数据
        new_model = {
            "id": "custom-model",
            "name": "Custom Model",
            "type": "openai",
            "model": "gpt-3.5-turbo",
            "api_key_name": "custom_api_key"
        }

        try:
            with app_context.test_request_context(json=new_model):
                response = model_manager.add_model()
                data, status_code = response if isinstance(response, tuple) else (response, 200)

            assert status_code == 200
            assert data.get_json()["success"] is True
            assert data.get_json()["message"] == "模型添加成功"
            assert data.get_json()["model"]["id"] == "custom-model"
            assert data.get_json()["model"]["api_key_name"] == "CUSTOM_API_KEY"  # 应该转大写
        finally:
            model_manager.MODELS_FILE = original_file

    def test_add_model_missing_required_field(self, temp_models_file, app_context):
        """测试缺少必填字段"""
        initial_data = {"version": "1.0.0", "models": [], "api_types": {}}
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        incomplete_model = {
            "id": "test",
            "name": "Test Model"
            # 缺少 type, model, api_key_name
        }

        try:
            with app_context.test_request_context(json=incomplete_model):
                response = model_manager.add_model()
                data, status_code = response if isinstance(response, tuple) else (response, 400)

            assert status_code == 400
            assert data.get_json()["success"] is False
            assert "缺少必填字段" in data.get_json()["message"]
        finally:
            model_manager.MODELS_FILE = original_file

    def test_add_model_duplicate_id(self, temp_models_file, app_context):
        """测试添加重复 ID 的模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [{"id": "existing-model", "name": "Existing"}],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        duplicate_model = {
            "id": "existing-model",
            "name": "Duplicate Model",
            "type": "openai",
            "model": "gpt-3.5-turbo",
            "api_key_name": "test_key"
        }

        try:
            with app_context.test_request_context(json=duplicate_model):
                response = model_manager.add_model()
                data, status_code = response if isinstance(response, tuple) else (response, 400)

            assert status_code == 400
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "模型ID已存在"
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.integration
class TestDeleteModel:
    """测试 delete_model 函数"""

    def test_delete_custom_model_success(self, temp_models_file, app_context):
        """测试成功删除自定义模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [
                {"id": "google", "name": "Google"},
                {"id": "custom-model", "name": "Custom"}
            ],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            with app_context.test_request_context():
                response = model_manager.delete_model("custom-model")
                data, status_code = response if isinstance(response, tuple) else (response, 200)

            assert status_code == 200
            assert data.get_json()["success"] is True
            assert data.get_json()["message"] == "模型删除成功"

            # 验证文件更新
            updated_data = model_manager.load_models()
            assert len(updated_data["models"]) == 1
            assert updated_data["models"][0]["id"] == "google"
        finally:
            model_manager.MODELS_FILE = original_file

    def test_delete_builtin_model_forbidden(self, temp_models_file, app_context):
        """测试不能删除内置模型"""
        builtin_models = ["google", "deepseek", "moonshot", "qwen", "spark"]

        # 为每个内置模型创建测试数据
        initial_models = [{"id": mid, "name": mid.title()} for mid in builtin_models]

        initial_data = {
            "version": "1.0.0",
            "models": initial_models,
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            for model_id in builtin_models:
                with app_context.test_request_context():
                    response = model_manager.delete_model(model_id)
                    data, status_code = response if isinstance(response, tuple) else (response, 400)

                assert status_code == 400, f"Expected 400 for {model_id}, got {status_code}"
                assert data.get_json()["success"] is False
                assert data.get_json()["message"] == "不能删除内置模型"
        finally:
            model_manager.MODELS_FILE = original_file

    def test_delete_model_not_found(self, temp_models_file, app_context):
        """测试删除不存在的模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            with app_context.test_request_context():
                response = model_manager.delete_model("nonexistent")
                data, status_code = response if isinstance(response, tuple) else (response, 404)

            assert status_code == 404
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "模型不存在"
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.integration
class TestUpdateModel:
    """测试 update_model 函数"""

    def test_update_custom_model_success(self, temp_models_file, app_context):
        """测试成功更新自定义模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [
                {
                    "id": "custom-model",
                    "name": "Old Name",
                    "type": "openai",
                    "model": "gpt-3.5-turbo",
                    "api_key_name": "OLD_KEY",
                    "enabled": True,
                    "icon": ""
                }
            ],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        update_data = {
            "name": "New Name",
            "type": "openai",
            "model": "gpt-4",
            "api_key_name": "new_key",
            "icon": "new-icon.svg",
            "base_url": "https://api.example.com"
        }

        try:
            with app_context.test_request_context(json=update_data):
                response = model_manager.update_model("custom-model")
                data, status_code = response if isinstance(response, tuple) else (response, 200)

            assert status_code == 200
            json_data = data.get_json()
            assert json_data["success"] is True
            assert json_data["message"] == "模型更新成功"
            assert json_data["model"]["name"] == "New Name"
            assert json_data["model"]["model"] == "gpt-4"
            assert json_data["model"]["api_key_name"] == "NEW_KEY"
            assert json_data["model"]["base_url"] == "https://api.example.com"
        finally:
            model_manager.MODELS_FILE = original_file

    def test_update_builtin_model_forbidden(self, temp_models_file, app_context):
        """测试不能修改内置模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [
                {"id": "google", "name": "Google", "type": "google", "model": "gemini", "api_key_name": "GOOGLE_API_KEY"}
            ],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        update_data = {
            "name": "Modified Google",
            "type": "google",
            "model": "gemini",
            "api_key_name": "GOOGLE_API_KEY"
        }

        try:
            with app_context.test_request_context(json=update_data):
                response = model_manager.update_model("google")
                data, status_code = response if isinstance(response, tuple) else (response, 400)

            assert status_code == 400
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "不能修改内置模型"
        finally:
            model_manager.MODELS_FILE = original_file

    def test_update_model_not_found(self, temp_models_file, app_context):
        """测试更新不存在的模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        update_data = {
            "name": "Test",
            "type": "openai",
            "model": "gpt-3.5-turbo",
            "api_key_name": "test_key"
        }

        try:
            with app_context.test_request_context(json=update_data):
                response = model_manager.update_model("nonexistent")
                data, status_code = response if isinstance(response, tuple) else (response, 404)

            assert status_code == 404
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "模型不存在"
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.integration
class TestGetModel:
    """测试 get_model 函数"""

    def test_get_model_success(self, temp_models_file, app_context):
        """测试成功获取模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [
                {"id": "google", "name": "Google Gemini", "type": "google"}
            ],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            with app_context.test_request_context():
                response = model_manager.get_model("google")
                data, status_code = response if isinstance(response, tuple) else (response, 200)

            assert status_code == 200
            json_data = data.get_json()
            assert json_data["success"] is True
            assert json_data["model"]["id"] == "google"
            assert json_data["model"]["name"] == "Google Gemini"
        finally:
            model_manager.MODELS_FILE = original_file

    def test_get_model_not_found(self, temp_models_file, app_context):
        """测试获取不存在的模型"""
        initial_data = {
            "version": "1.0.0",
            "models": [],
            "api_types": {}
        }
        with open(temp_models_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        original_file = model_manager.MODELS_FILE
        model_manager.MODELS_FILE = temp_models_file

        try:
            with app_context.test_request_context():
                response = model_manager.get_model("nonexistent")
                data, status_code = response if isinstance(response, tuple) else (response, 404)

            assert status_code == 404
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "模型不存在"
        finally:
            model_manager.MODELS_FILE = original_file


@pytest.mark.integration
class TestUploadIcon:
    """测试 upload_icon 函数"""

    def test_upload_icon_success(self, temp_icons_dir, app_context):
        """测试成功上传图标"""
        original_icons_dir = model_manager.ICONS_DIR
        model_manager.ICONS_DIR = temp_icons_dir

        # 模拟文件上传 - 使用 FileStorage 对象
        from io import BytesIO
        from werkzeug.datastructures import FileStorage

        file_content = b"fake image content"
        file_obj = FileStorage(
            stream=BytesIO(file_content),
            filename="test_icon.png",
            content_type="image/png"
        )

        try:
            with app_context.test_request_context():
                # 直接修改 request.files
                from flask import request
                request.files = {'file': file_obj}

                response = model_manager.upload_icon()
                data, status_code = response if isinstance(response, tuple) else (response, 200)

            assert status_code == 200
            json_data = data.get_json()
            assert json_data["success"] is True
            assert json_data["message"] == "图标上传成功"
            assert "filename" in json_data
            assert ".png" in json_data["filename"]
            assert json_data["url"].startswith("/assets/icons/")
        finally:
            model_manager.ICONS_DIR = original_icons_dir

    def test_upload_icon_no_file(self, app_context):
        """测试没有上传文件"""
        with app_context.test_request_context():
            from flask import request
            request.files = {}

            response = model_manager.upload_icon()
            data, status_code = response if isinstance(response, tuple) else (response, 400)

        assert status_code == 400
        assert data.get_json()["success"] is False
        assert data.get_json()["message"] == "没有文件"

    def test_upload_icon_empty_filename(self, temp_icons_dir, app_context):
        """测试空文件名"""
        original_icons_dir = model_manager.ICONS_DIR
        model_manager.ICONS_DIR = temp_icons_dir

        from io import BytesIO
        from werkzeug.datastructures import FileStorage

        file_obj = FileStorage(
            stream=BytesIO(b""),
            filename="",
            content_type="image/png"
        )

        try:
            with app_context.test_request_context():
                from flask import request
                request.files = {'file': file_obj}

                response = model_manager.upload_icon()
                data, status_code = response if isinstance(response, tuple) else (response, 400)

            assert status_code == 400
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "没有选择文件"
        finally:
            model_manager.ICONS_DIR = original_icons_dir

    def test_upload_icon_invalid_extension(self, temp_icons_dir, app_context):
        """测试无效的文件扩展名"""
        original_icons_dir = model_manager.ICONS_DIR
        model_manager.ICONS_DIR = temp_icons_dir

        from io import BytesIO
        from werkzeug.datastructures import FileStorage

        file_obj = FileStorage(
            stream=BytesIO(b"fake content"),
            filename="test.exe",
            content_type="application/exe"
        )

        try:
            with app_context.test_request_context():
                from flask import request
                request.files = {'file': file_obj}

                response = model_manager.upload_icon()
                data, status_code = response if isinstance(response, tuple) else (response, 400)

            assert status_code == 400
            assert data.get_json()["success"] is False
            assert data.get_json()["message"] == "不支持的文件类型"
        finally:
            model_manager.ICONS_DIR = original_icons_dir


@pytest.mark.integration
class TestRegisterRoutes:
    """测试 register_routes 函数"""

    def test_register_routes(self, app_context):
        """测试路由注册"""
        from flask import Flask

        # 创建独立的 Flask 应用来测试路由注册
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True

        model_manager.register_routes(test_app)

        # 收集路由和方法
        route_methods = {}
        for rule in test_app.url_map.iter_rules():
            if rule.rule not in route_methods:
                route_methods[rule.rule] = set()
            route_methods[rule.rule].update(rule.methods - {'HEAD', 'OPTIONS'})

        # 验证路由已注册
        assert "/api/models/list" in route_methods
        assert "/api/models/<model_id>" in route_methods
        assert "/api/models" in route_methods
        assert "/api/models/icon/upload" in route_methods

        # 验证 HTTP 方法（去除 HEAD 和 OPTIONS）
        assert route_methods["/api/models/list"] == {"GET"}
        assert route_methods["/api/models"] == {"POST"}
        assert route_methods["/api/models/<model_id>"] == {"GET", "DELETE", "PUT"}
        assert route_methods["/api/models/icon/upload"] == {"POST"}
