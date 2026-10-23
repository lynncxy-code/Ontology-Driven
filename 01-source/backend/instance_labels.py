"""Type-owned, opt-in plain labels. Independent of popup/overlay configuration."""

DEFAULT_LABEL = {"enabled": False, "source": "instance_name", "field": "", "text": ""}


def label_config(object_type):
    visual = (object_type.get("interface_configs") or {}).get("I3D_Visual") or {}
    stored = visual.get("label") or {}
    return {**DEFAULT_LABEL, **{k: stored[k] for k in DEFAULT_LABEL if k in stored}}


def resolve_label(object_type, instance, raw):
    config = label_config(object_type)
    if "I3D_Visual" not in object_type.get("injected_interfaces", []) or config["enabled"] is not True:
        return ""
    if config["source"] == "field":
        value = raw.get(config["field"])
    elif config["source"] == "fixed":
        value = config["text"]
    else:
        value = instance.get("display_name") or instance.get("id") or ""
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value)[:256]


def register_label_routes(app, get_types, persist):
    from flask import jsonify, request

    @app.route('/api/v2/ontology/types/<object_type_rid>/label-config', methods=['PUT'])
    def save_type_label(object_type_rid):
        obj = get_types().get(object_type_rid)
        if obj is None:
            return jsonify({"error": "类型不存在"}), 404
        if "I3D_Visual" not in obj.get("injected_interfaces", []):
            return jsonify({"error": "请先启用外观表现能力"}), 400
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            return jsonify({"error": "标签显示设置无效"}), 400
        config = {k: data.get(k, v) for k, v in DEFAULT_LABEL.items()}
        if not isinstance(config["source"], str) or config["source"] not in {"instance_name", "field", "fixed"}:
            return jsonify({"error": "请选择有效的文字来源"}), 400
        if not all(isinstance(config[k], str) and len(config[k]) <= 256 for k in ("field", "text")):
            return jsonify({"error": "标签文字最长 256 个字符"}), 400
        fields = {p["name"] for p in obj.get("properties", []) if p.get("name")}
        if config["enabled"] and config["source"] == "field" and config["field"] not in fields:
            return jsonify({"error": "请选择该类型已有的业务字段"}), 400
        if config["enabled"] and config["source"] == "fixed" and not config["text"].strip():
            return jsonify({"error": "请填写标签文字，或关闭文字标签"}), 400
        obj.setdefault("interface_configs", {}).setdefault("I3D_Visual", {})["label"] = config
        persist()
        return jsonify({"label": config})
