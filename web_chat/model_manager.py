"""
模型管理模块

提供模型的增删改查功能，包括：
- 加载和保存模型配置
- 添加、删除、更新、查询模型
- 上传模型图标
- 文件类型验证
"""
import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from flask import jsonify, request, Response
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# 配置日志
logger = logging.getLogger(__name__)

# 模块常量
MODELS_FILE: str = os.path.join(os.path.dirname(__file__), "models.json")
MODELS_EXAMPLE_FILE: str = os.path.join(os.path.dirname(__file__), "models.json.example")
ICONS_DIR: str = os.path.join(os.path.dirname(__file__), "assets", "icons")
ALLOWED_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "svg", "gif"}


def load_models() -> Dict[str, Any]:
    """加载模型配置文件

    如果 models.json 不存在，会尝试从 models.json.example 复制初始配置。
    如果两个文件都不存在或格式错误，返回默认空配置。

    Returns:
        Dict[str, Any]: 包含 version, models, api_types 的配置字典

    Examples:
        >>> data = load_models()
        >>> data["version"]
        '1.0.0'
        >>> data["models"]
        [...]
    """
    # 如果 models.json 不存在，从 example 文件复制
    if not os.path.exists(MODELS_FILE):
        if os.path.exists(MODELS_EXAMPLE_FILE):
            try:
                import shutil
                shutil.copy2(MODELS_EXAMPLE_FILE, MODELS_FILE)
                logger.info(f"Initialized {MODELS_FILE} from {MODELS_EXAMPLE_FILE}")
            except IOError as e:
                logger.error(f"Failed to copy example file: {e}")
                return {"version": "1.0.0", "models": [], "api_types": {}}
        else:
            logger.warning("No models configuration file found, using defaults")
            return {"version": "1.0.0", "models": [], "api_types": {}}

    try:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load models file: {e}")
        return {"version": "1.0.0", "models": [], "api_types": {}}


def save_models(data: Dict[str, Any]) -> bool:
    """保存模型配置到文件

    Args:
        data: 要保存的配置字典，包含 version, models, api_types

    Returns:
        bool: 保存成功返回 True，失败返回 False

    Examples:
        >>> data = {"version": "1.0.0", "models": [], "api_types": {}}
        >>> save_models(data)
        True
    """
    try:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved models configuration to {MODELS_FILE}")
        return True
    except IOError as e:
        logger.error(f"Failed to save models file: {e}")
        return False


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许

    Args:
        filename: 文件名

    Returns:
        bool: 扩展名在允许列表中返回 True

    Examples:
        >>> allowed_file("test.png")
        True
        >>> allowed_file("test.exe")
        False
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_all_models() -> Response:
    """获取所有模型和 API 类型列表

    Returns:
        Response: JSON 响应，包含 success, models, api_types

    Examples:
        >>> response = get_all_models()
        >>> data = response.get_json()
        >>> data["success"]
        True
    """
    data = load_models()
    return jsonify({
        "success": True,
        "models": data.get("models", []),
        "api_types": data.get("api_types", {})
    })


def add_model() -> Union[Tuple[Response, int], Response]:
    """添加新模型

    请求 JSON 参数:
        id (str): 模型唯一标识符
        name (str): 模型显示名称
        type (str): API 类型 (google, openai, requests_sse, spark_requests)
        model (str): API 使用的模型名称
        api_key_name (str): API 密钥的环境变量名
        icon (str, optional): 图标文件名
        base_url (str, optional): API 基础 URL (openai 类型)
        url (str, optional): 完整 API URL (requests_sse/spark_requests 类型)
        system (str, optional): 系统提示词 (openai 类型)

    Returns:
        Union[Tuple[Response, int], Response]:
            成功: (Response, 200)
            失败: (Response, 400) 或 (Response, 500)

    Examples:
        >>> # 添加 OpenAI 兼容模型
        >>> new_model = {
        ...     "id": "custom-gpt",
        ...     "name": "Custom GPT",
        ...     "type": "openai",
        ...     "model": "gpt-3.5-turbo",
        ...     "api_key_name": "custom_key"
        ... }
        >>> response, status = add_model()
    """
    model_data = request.json
    required_fields = ["id", "name", "type", "model", "api_key_name"]

    # 验证必填字段
    for field in required_fields:
        if field not in model_data or not model_data[field]:
            return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400

    data = load_models()
    models = data.get("models", [])

    # 检查 ID 是否重复
    for model in models:
        if model["id"] == model_data["id"]:
            return jsonify({"success": False, "message": "模型ID已存在"}), 400

    # 创建新模型
    new_model = {
        "id": model_data["id"],
        "name": model_data["name"],
        "type": model_data["type"],
        "model": model_data["model"],
        "api_key_name": model_data["api_key_name"].upper(),
        "enabled": True,
        "icon": model_data.get("icon", ""),
    }

    # 添加可选字段
    if "base_url" in model_data:
        new_model["base_url"] = model_data["base_url"]
    if "url" in model_data:
        new_model["url"] = model_data["url"]
    if "system" in model_data:
        new_model["system"] = model_data["system"]

    models.append(new_model)
    data["models"] = models

    if save_models(data):
        logger.info(f"Added new model: {new_model['id']}")
        return jsonify({"success": True, "message": "模型添加成功", "model": new_model})
    else:
        return jsonify({"success": False, "message": "保存失败"}), 500


def delete_model(model_id: str) -> Union[Tuple[Response, int], Response]:
    """删除模型

    内置模型 (google, deepseek, moonshot, qwen, spark) 不能删除。

    Args:
        model_id: 要删除的模型 ID

    Returns:
        Union[Tuple[Response, int], Response]:
            成功: (Response, 200)
            失败: (Response, 400) 或 (Response, 404) 或 (Response, 500)

    Examples:
        >>> response, status = delete_model("custom-model")
        >>> response.get_json()["success"]
        True
    """
    data = load_models()
    models = data.get("models", [])

    for i, model in enumerate(models):
        if model["id"] == model_id:
            # 检查是否是内置模型
            if model["id"] in ["google", "deepseek", "moonshot", "qwen", "spark"]:
                logger.warning(f"Attempted to delete built-in model: {model_id}")
                return jsonify({"success": False, "message": "不能删除内置模型"}), 400

            models.pop(i)
            data["models"] = models

            if save_models(data):
                logger.info(f"Deleted model: {model_id}")
                return jsonify({"success": True, "message": "模型删除成功"})
            else:
                return jsonify({"success": False, "message": "保存失败"}), 500

    return jsonify({"success": False, "message": "模型不存在"}), 404


def update_model(model_id: str) -> Union[Tuple[Response, int], Response]:
    """更新模型配置

    内置模型不能修改。只有自定义模型可以更新。

    Args:
        model_id: 要更新的模型 ID

    请求 JSON 参数:
        name (str): 模型显示名称
        type (str): API 类型
        model (str): API 使用的模型名称
        api_key_name (str): API 密钥的环境变量名
        icon (str, optional): 图标文件名
        base_url (str, optional): API 基础 URL
        url (str, optional): 完整 API URL
        system (str, optional): 系统提示词

    Returns:
        Union[Tuple[Response, int], Response]:
            成功: (Response, 200)
            失败: (Response, 400) 或 (Response, 404) 或 (Response, 500)

    Examples:
        >>> update_data = {"name": "New Name", "type": "openai", ...}
        >>> response, status = update_model("custom-model")
    """
    model_data = request.json
    required_fields = ["name", "type", "model", "api_key_name"]

    # 验证必填字段
    for field in required_fields:
        if field not in model_data or not model_data[field]:
            return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400

    data = load_models()
    models = data.get("models", [])

    # 查找并更新模型
    for i, model in enumerate(models):
        if model["id"] == model_id:
            # 检查是否是内置模型
            if model_id in ["google", "deepseek", "moonshot", "qwen", "spark"]:
                logger.warning(f"Attempted to modify built-in model: {model_id}")
                return jsonify({"success": False, "message": "不能修改内置模型"}), 400

            # 更新必填字段
            models[i]["name"] = model_data["name"]
            models[i]["type"] = model_data["type"]
            models[i]["model"] = model_data["model"]
            models[i]["api_key_name"] = model_data["api_key_name"].upper()
            models[i]["icon"] = model_data.get("icon", "")

            # 更新可选字段
            if "base_url" in model_data:
                models[i]["base_url"] = model_data["base_url"]
            elif "base_url" in models[i]:
                del models[i]["base_url"]

            if "url" in model_data:
                models[i]["url"] = model_data["url"]
            elif "url" in models[i]:
                del models[i]["url"]

            if "system" in model_data:
                models[i]["system"] = model_data["system"]
            elif "system" in models[i]:
                del models[i]["system"]

            data["models"] = models

            if save_models(data):
                logger.info(f"Updated model: {model_id}")
                return jsonify({"success": True, "message": "模型更新成功", "model": models[i]})
            else:
                return jsonify({"success": False, "message": "保存失败"}), 500

    return jsonify({"success": False, "message": "模型不存在"}), 404


def get_model(model_id: str) -> Union[Tuple[Response, int], Response]:
    """获取单个模型的详细信息

    Args:
        model_id: 模型 ID

    Returns:
        Union[Tuple[Response, int], Response]:
            成功: (Response, 200)
            失败: (Response, 404)

    Examples:
        >>> response = get_model("google")
        >>> data = response.get_json()
        >>> data["model"]["name"]
        'Google Gemini'
    """
    data = load_models()
    models = data.get("models", [])

    for model in models:
        if model["id"] == model_id:
            return jsonify({"success": True, "model": model})

    return jsonify({"success": False, "message": "模型不存在"}), 404


def upload_icon() -> Union[Tuple[Response, int], Response]:
    """上传模型图标文件

    支持的文件格式: png, jpg, jpeg, svg, gif
    文件名会添加随机后缀以避免冲突。

    Returns:
        Union[Tuple[Response, int], Response]:
            成功: (Response, 200) 包含 filename 和 url
            失败: (Response, 400)

    Examples:
        >>> # 上传成功
        >>> response = upload_icon()
        >>> data = response.get_json()
        >>> data["filename"]
        'test_icon_abc123.png'
        >>> data["url"]
        '/assets/icons/test_icon_abc123.png'
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "没有文件"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "message": "没有选择文件"}), 400

    if not allowed_file(file.filename):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"success": False, "message": "不支持的文件类型"}), 400

    # 确保目录存在
    os.makedirs(ICONS_DIR, exist_ok=True)

    # 生成唯一文件名
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(ICONS_DIR, unique_filename)

    # 保存文件
    file.save(filepath)
    logger.info(f"Uploaded icon: {unique_filename}")

    return jsonify({
        "success": True,
        "message": "图标上传成功",
        "filename": unique_filename,
        "url": f"/assets/icons/{unique_filename}"
    })


def register_routes(app, limiter=None) -> None:
    """注册模型管理相关的 API 路由

    Args:
        app: Flask 应用实例
        limiter: Flask-Limiter 实例（可选），用于速率限制

    注册的路由:
        GET  /api/models/list - 获取所有模型列表
        GET  /api/models/<model_id> - 获取单个模型详情
        POST /api/models - 添加新模型
        PUT  /api/models/<model_id> - 更新模型
        DELETE /api/models/<model_id> - 删除模型
        POST /api/models/icon/upload - 上传模型图标

    Examples:
        >>> from flask import Flask
        >>> app = Flask(__name__)
        >>> register_routes(app)
        >>> # 或带速率限制
        >>> from flask_limiter import Limiter
        >>> limiter = Limiter(app)
        >>> register_routes(app, limiter)
    """
    # 速率限制辅助函数（根据环境调整限制）
    def rate_limit(limit_string: str):
        """根据环境返回速率限制装饰器

        Args:
            limit_string: 限制字符串，如 "10 per minute"

        Returns:
            装饰器函数或恒等函数
        """
        if limiter is None:
            # 没有 limiter 实例，返回恒等函数
            return lambda f: f
        if app.config.get('TESTING'):
            # 测试环境：使用极高的限制
            return limiter.limit("10000 per minute")
        else:
            # 生产环境：使用指定的限制
            return limiter.limit(limit_string)
    @app.route("/api/models/list", methods=["GET"])
    def api_get_models() -> Response:
        return get_all_models()

    @app.route("/api/models/<model_id>", methods=["GET"])
    def api_get_model(model_id: str) -> Union[Tuple[Response, int], Response]:
        return get_model(model_id)

    # 添加模型的速率限制装饰器
    add_model_limited = rate_limit("5 per minute")(add_model)

    @app.route("/api/models", methods=["POST"])
    def api_add_model() -> Union[Tuple[Response, int], Response]:
        return add_model_limited()

    # 删除模型的速率限制装饰器
    delete_model_limited = rate_limit("10 per minute")(delete_model)

    @app.route("/api/models/<model_id>", methods=["DELETE"])
    def api_delete_model(model_id: str) -> Union[Tuple[Response, int], Response]:
        return delete_model_limited(model_id)

    # 更新模型的速率限制装饰器
    update_model_limited = rate_limit("10 per minute")(update_model)

    @app.route("/api/models/<model_id>", methods=["PUT"])
    def api_update_model(model_id: str) -> Union[Tuple[Response, int], Response]:
        return update_model_limited(model_id)

    # 上传图标的速率限制装饰器
    upload_icon_limited = rate_limit("10 per minute")(upload_icon)

    @app.route("/api/models/icon/upload", methods=["POST"])
    def api_upload_icon() -> Union[Tuple[Response, int], Response]:
        return upload_icon_limited()

    logger.debug("Registered model management routes")
