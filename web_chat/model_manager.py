"""
模型管理模块
提供模型的增删改查功能
"""
import os
import json
import uuid
from flask import jsonify, request
from werkzeug.utils import secure_filename

MODELS_FILE = os.path.join(os.path.dirname(__file__), "models.json")
MODELS_EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "models.json.example")
ICONS_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "svg", "gif"}


def load_models():
    # 如果 models.json 不存在，从 example 文件复制
    if not os.path.exists(MODELS_FILE):
        if os.path.exists(MODELS_EXAMPLE_FILE):
            try:
                import shutil
                shutil.copy2(MODELS_EXAMPLE_FILE, MODELS_FILE)
                print(f"Initialized {MODELS_FILE} from {MODELS_EXAMPLE_FILE}", flush=True)
            except IOError as e:
                print(f"Failed to copy example file: {e}", flush=True)
                return {"version": "1.0.0", "models": [], "api_types": {}}
        else:
            return {"version": "1.0.0", "models": [], "api_types": {}}

    try:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"version": "1.0.0", "models": [], "api_types": {}}


def save_models(data):
    try:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_all_models():
    data = load_models()
    return jsonify({
        "success": True,
        "models": data.get("models", []),
        "api_types": data.get("api_types", {})
    })


def add_model():
    model_data = request.json
    required_fields = ["id", "name", "type", "model", "api_key_name"]
    for field in required_fields:
        if field not in model_data or not model_data[field]:
            return jsonify({"success": False, "message": f"缺少必填字段: {field}"}), 400
    data = load_models()
    models = data.get("models", [])
    for model in models:
        if model["id"] == model_data["id"]:
            return jsonify({"success": False, "message": "模型ID已存在"}), 400
    new_model = {
        "id": model_data["id"],
        "name": model_data["name"],
        "type": model_data["type"],
        "model": model_data["model"],
        "api_key_name": model_data["api_key_name"].upper(),
        "enabled": True,
        "icon": model_data.get("icon", ""),
    }
    if "base_url" in model_data:
        new_model["base_url"] = model_data["base_url"]
    if "url" in model_data:
        new_model["url"] = model_data["url"]
    if "system" in model_data:
        new_model["system"] = model_data["system"]
    models.append(new_model)
    data["models"] = models
    if save_models(data):
        return jsonify({"success": True, "message": "模型添加成功", "model": new_model})
    else:
        return jsonify({"success": False, "message": "保存失败"}), 500


def delete_model(model_id):
    data = load_models()
    models = data.get("models", [])
    for i, model in enumerate(models):
        if model["id"] == model_id:
            if model["id"] in ["google", "deepseek", "moonshot", "qwen", "spark"]:
                return jsonify({"success": False, "message": "不能删除内置模型"}), 400
            models.pop(i)
            data["models"] = models
            if save_models(data):
                return jsonify({"success": True, "message": "模型删除成功"})
            else:
                return jsonify({"success": False, "message": "保存失败"}), 500
    return jsonify({"success": False, "message": "模型不存在"}), 404


def update_model(model_id):
    """更新模型配置"""
    model_data = request.json
    required_fields = ["name", "type", "model", "api_key_name"]
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
                return jsonify({"success": False, "message": "不能修改内置模型"}), 400

            # 更新字段
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
                return jsonify({"success": True, "message": "模型更新成功", "model": models[i]})
            else:
                return jsonify({"success": False, "message": "保存失败"}), 500

    return jsonify({"success": False, "message": "模型不存在"}), 404


def get_model(model_id):
    """获取单个模型的详细信息"""
    data = load_models()
    models = data.get("models", [])
    for model in models:
        if model["id"] == model_id:
            return jsonify({"success": True, "model": model})
    return jsonify({"success": False, "message": "模型不存在"}), 404


def upload_icon():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "没有文件"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "没有选择文件"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "不支持的文件类型"}), 400
    os.makedirs(ICONS_DIR, exist_ok=True)
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(ICONS_DIR, unique_filename)
    file.save(filepath)
    return jsonify({
        "success": True,
        "message": "图标上传成功",
        "filename": unique_filename,
        "url": f"/assets/icons/{unique_filename}"
    })


def register_routes(app):
    @app.route("/api/models/list", methods=["GET"])
    def api_get_models():
        return get_all_models()

    @app.route("/api/models/<model_id>", methods=["GET"])
    def api_get_model(model_id):
        return get_model(model_id)

    @app.route("/api/models", methods=["POST"])
    def api_add_model():
        return add_model()

    @app.route("/api/models/<model_id>", methods=["DELETE"])
    def api_delete_model(model_id):
        return delete_model(model_id)

    @app.route("/api/models/<model_id>", methods=["PUT"])
    def api_update_model(model_id):
        return update_model(model_id)

    @app.route("/api/models/icon/upload", methods=["POST"])
    def api_upload_icon():
        return upload_icon()
