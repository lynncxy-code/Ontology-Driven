import os
import time
import math
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from ontology import SharedState
from mapping_store import (
    MappingStore, ONTOLOGY_PROPERTIES, INTERFACES, INTERFACE_MAP,
    TRANSFORM_TYPES, MOCK_ASSETS, OBJECT_TYPES,
    InstanceStore, MockInstanceSimulator
)

# ── App Setup ───────────────────────────────────────────────────
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ── Global State ────────────────────────────────────────────────
# 旧版 1.x 状态（兼容）
states = {
    "vehicle_01": SharedState(),
    "equipment_01": SharedState(),
    "tooling_01": SharedState()
}
mapping_store = MappingStore()

# 2.3 新版：动态实例系统
instance_store = InstanceStore()
simulator = MockInstanceSimulator(instance_store)
simulator.start()

# ObjectType 接口注册表（运行时内存，初始化自 OBJECT_TYPES）
_object_types = {k: dict(v) for k, v in OBJECT_TYPES.items()}

# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/nexus')
def serve_nexus():
    return app.send_static_file('nexus.html')

@app.route('/ontology')
def serve_ontology():
    return app.send_static_file('ontology.html')

@app.route('/instance')
def serve_instance():
    return app.send_static_file('instance.html')

@app.route('/mapping')
def serve_mapping():
    return app.send_static_file('mapping.html')

@app.route('/ontology_graph')
def serve_ontology_graph():
    return app.send_static_file('ontology_graph.html')

@app.route('/coming_soon.html')
def serve_coming_soon():
    return app.send_static_file('coming_soon.html')


# ═══════════════════════════════════════════════════════════════
# 旧版 1.x API（兼容保留）
# ═══════════════════════════════════════════════════════════════

@app.route('/api/state', methods=['GET'])
def get_state():
    instance_id = request.args.get('id', 'vehicle_01')
    target_state = states.get(instance_id)
    if not target_state:
        return jsonify({"error": "Instance not found"}), 404
    data = target_state.to_dict()
    data['asset_id'] = instance_id
    return jsonify(data)

@app.route('/api/update', methods=['POST'])
def update_state():
    data = request.json
    instance_id = request.args.get('id') or data.get('id', 'vehicle_01')
    target_state = states.get(instance_id)
    if not target_state:
        return jsonify({"error": "Instance not found"}), 404
    for key in ['translation_x', 'translation_y', 'translation_z',
                'rotation_x', 'rotation_y', 'rotation_z',
                'scale_x', 'scale_y', 'scale_z']:
        if key in data and data[key] is not None:
            try:
                data[key] = float(data[key])
            except (ValueError, TypeError):
                pass
    import time as _time
    data['timestamp'] = _time.time()
    target_state.update(data)
    ret_data = target_state.to_dict()
    ret_data['asset_id'] = instance_id
    return jsonify(ret_data)


# ═══════════════════════════════════════════════════════════════
# 2.3 API — 本体对象类型 (ObjectType Registry)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/ontology/types', methods=['GET'])
def get_object_types():
    """获取所有 ObjectType 及其接口挂载状态"""
    result = []
    for rid, ot in _object_types.items():
        result.append({
            "rid": ot["rid"],
            "name": ot["name"],
            "category": ot["category"],
            "description": ot["description"],
            "color": ot.get("color", "#888888"),
            "properties": ot["properties"],
            "injected_interfaces": ot.get("injected_interfaces", []),
            "asset_id": ot.get("asset_id"),
            "mock_instances": ot.get("mock_instances", []),
            "has_representable": "I3D_Representable" in ot.get("injected_interfaces", [])
        })
    return jsonify(result)

@app.route('/api/v2/ontology/types/<object_type_rid>', methods=['GET'])
def get_object_type(object_type_rid):
    """获取单个 ObjectType"""
    ot = _object_types.get(object_type_rid)
    if not ot:
        return jsonify({"error": "ObjectType not found"}), 404
    return jsonify(ot)

@app.route('/api/v2/ontology/inject', methods=['POST'])
def inject_interfaces():
    """
    为 ObjectType 挂载能力接口。
    Body: { "object_type_rid": str, "interfaces": [str], "asset_id": str (optional) }
    """
    data = request.json or {}
    rid = data.get("object_type_rid")
    interfaces = data.get("interfaces", [])

    if not rid:
        return jsonify({"error": "object_type_rid is required"}), 400
    if rid not in _object_types:
        return jsonify({"error": f"ObjectType '{rid}' not found"}), 404

    # 校验：若要挂载子接口，必须先有 I3D_Representable
    current = set(_object_types[rid].get("injected_interfaces", []))
    adding = set(interfaces)
    child_ifaces = {"I3D_Spatial", "I3D_Visual", "I3D_Behavioral"}
    if adding & child_ifaces and "I3D_Representable" not in (current | adding):
        return jsonify({"error": "子能力接口需要先挂载 I3D_Representable"}), 400

    # 合并（追加，不覆盖）
    merged = list(current | adding)
    # 保证 I3D_Representable 在首位
    if "I3D_Representable" in merged:
        merged = ["I3D_Representable"] + [i for i in merged if i != "I3D_Representable"]

    _object_types[rid]["injected_interfaces"] = merged

    # 如果同时传了 asset_id，一并保存
    if "asset_id" in data and data["asset_id"]:
        _object_types[rid]["asset_id"] = data["asset_id"]

    return jsonify({
        "object_type_rid": rid,
        "injected_interfaces": merged,
        "asset_id": _object_types[rid].get("asset_id")
    })

@app.route('/api/v2/ontology/inject', methods=['DELETE'])
@app.route('/api/v2/ontology/inject/remove', methods=['POST', 'DELETE'])
def remove_interface():
    """
    从 ObjectType 移除某接口。
    Body: { "object_type_rid": str, "interface_rid": str }
    注意：移除 I3D_Representable 会同时移除所有子接口。
    """
    data = request.json or {}
    rid = request.args.get("object_type_rid") or data.get("object_type_rid")
    iface = request.args.get("interface_rid") or data.get("interface_rid")
    if not rid or not iface:
        return jsonify({"error": "object_type_rid and interface_rid are required"}), 400
    if rid not in _object_types:
        return jsonify({"error": "ObjectType not found"}), 404

    current = list(_object_types[rid].get("injected_interfaces", []))
    if iface == "I3D_Representable":
        # 移除顶层接口，级联删除所有子接口
        current = []
        _object_types[rid]["asset_id"] = None
    else:
        current = [i for i in current if i != iface]
    _object_types[rid]["injected_interfaces"] = current
    return jsonify({"object_type_rid": rid, "injected_interfaces": current})


# ═══════════════════════════════════════════════════════════════
# 2.3 API — 接口定义查询
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/ontology/interfaces', methods=['GET'])
def get_ontology_interfaces():
    """获取全部能力接口定义（含两层结构信息）"""
    return jsonify(INTERFACES)

@app.route('/api/v2/ontology/properties', methods=['GET'])
def get_ontology_properties():
    return jsonify(ONTOLOGY_PROPERTIES)

@app.route('/api/v2/transforms', methods=['GET'])
def get_transform_types():
    return jsonify(TRANSFORM_TYPES)


# ═══════════════════════════════════════════════════════════════
# 2.3 API — 资产管理 (Asset Registry)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/assets', methods=['GET'])
def list_assets():
    """返回资产库所有资产列表（供前端资产库卡片选择）"""
    result = []
    for fn, meta in MOCK_ASSETS.items():
        result.append({
            "file_number":  fn,
            "name":         meta.get("name", fn),
            "format":       meta.get("format", "glb"),
            "bounding_box": meta.get("bounding_box", {}),
            "download_url": meta.get("download_url", "")
        })
    return jsonify(result)

@app.route('/api/v2/assets/bind', methods=['POST'])
def bind_asset():
    """
    绑定 GLB 资产到 ObjectType。
    Body: { "object_type_rid": str, "file_number": str }
    """
    data = request.json or {}
    rid = data.get("object_type_rid")
    file_number = data.get("file_number", "").strip()

    if not rid or not file_number:
        return jsonify({"error": "object_type_rid and file_number are required"}), 400
    if rid not in _object_types:
        return jsonify({"error": "ObjectType not found"}), 404

    # 校验 FileNumber
    asset_meta = MOCK_ASSETS.get(file_number)
    valid = asset_meta is not None
    warning = None if valid else f"资产库中未找到编号 '{file_number}'，请确认后再绑定。"

    _object_types[rid]["asset_id"] = file_number
    return jsonify({
        "object_type_rid": rid,
        "file_number":     file_number,
        "valid":           valid,
        "warning":         warning,
        "name":            asset_meta.get("name", "") if asset_meta else "",
        "format":          asset_meta.get("format", "") if asset_meta else "",
        "bounding_box":    asset_meta.get("bounding_box", {}) if asset_meta else {}
    })


@app.route('/api/v2/assets/resolve', methods=['GET'])
def resolve_asset():
    """通过 file_number 获取 GLB 资产元数据与下载地址"""
    file_number = request.args.get("file_number", "")
    if not file_number:
        return jsonify({"error": "file_number is required"}), 400
    asset = MOCK_ASSETS.get(file_number)
    if not asset:
        return jsonify({"error": f"Asset '{file_number}' not found", "valid": False}), 404
    return jsonify({"valid": True, **asset})


# ═══════════════════════════════════════════════════════════════
# 2.3 API — 实例管理 (Instance Lifecycle)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/instances', methods=['GET'])
def list_instances():
    """获取所有实例清单（含在线状态）"""
    return jsonify(instance_store.list_all())

@app.route('/api/v2/instances', methods=['POST'])
def spawn_instance():
    """
    投产新实例。
    Body: { "instance_id": str, "object_type_rid": str,
            "initial_position": {"x": float, "y": float, "z": float} }
    """
    data = request.json or {}
    instance_id = data.get("instance_id", "").strip()
    object_type_rid = data.get("object_type_rid", "").strip()
    initial_position = data.get("initial_position", {"x": 0, "y": 0, "z": 0})

    if not instance_id:
        return jsonify({"error": "instance_id is required"}), 400
    if not object_type_rid:
        return jsonify({"error": "object_type_rid is required"}), 400
    if object_type_rid not in _object_types:
        return jsonify({"error": f"ObjectType '{object_type_rid}' not found"}), 404
    if not _object_types[object_type_rid].get("injected_interfaces"):
        return jsonify({"error": "该 ObjectType 尚未挂载任何三维接口，请先在本体注入中心配置。"}), 400

    existing = instance_store.get_raw_state(instance_id)
    if existing is not None:
        return jsonify({"error": f"实例 ID '{instance_id}' 已存在"}), 409

    inst = instance_store.spawn(instance_id, object_type_rid, initial_position)
    return jsonify({"status": "spawned", "instance": inst}), 201

@app.route('/api/v2/instances/<path:instance_id>', methods=['DELETE'])
@app.route('/api/v2/instances/<path:instance_id>/delete', methods=['POST', 'DELETE'])
def delete_instance(instance_id):
    """销毁实例"""
    removed = instance_store.remove(instance_id)
    if removed:
        return jsonify({"status": "removed", "id": instance_id})
    return jsonify({"error": "Instance not found"}), 404

@app.route('/api/v2/instances/<path:instance_id>', methods=['GET'])
def get_instance(instance_id):
    """获取单实例信息"""
    raw = instance_store.get_raw_state(instance_id)
    if raw is None:
        return jsonify({"error": "Instance not found"}), 404
    all_list = instance_store.list_all()
    meta = next((i for i in all_list if i["id"] == instance_id), None)
    return jsonify({"id": instance_id, **(meta or {}), "raw_state": raw})


# ═══════════════════════════════════════════════════════════════
# 2.3 API — 状态快照 & Override
# ═══════════════════════════════════════════════════════════════

def _build_snapshot(instance_id):
    """根据 ObjectType 接口配置，将 raw_state 组装为标准接口格式快照。"""
    raw = instance_store.get_raw_state(instance_id)
    if raw is None:
        return None

    # 找 ObjectType
    all_instances = instance_store.list_all()
    inst_meta = next((i for i in all_instances if i["id"] == instance_id), {})
    ot_rid = inst_meta.get("object_type_rid", "")
    ot = _object_types.get(ot_rid, {})
    injected = ot.get("injected_interfaces", [])
    asset_id = ot.get("asset_id") or raw.get("asset_id", "")
    # 将 file_number 解析为 UE 内容路径（供 3D 渲染端 LoadObject 使用）
    asset_meta = MOCK_ASSETS.get(asset_id, {})
    ue_asset_path = asset_meta.get("ue_path", asset_id)  # fallback: 原始 asset_id

    now = time.time()
    online = (now - inst_meta.get("last_seen", 0)) < 3.0

    interfaces = {}

    if "I3D_Representable" in injected:
        interfaces["I3D_Representable"] = {
            "asset_id": ue_asset_path,
            "file_number": asset_id,
            "is_visible": raw.get("is_loaded", True)
        }

    if "I3D_Spatial" in injected:
        interfaces["I3D_Spatial"] = {
            "translation_x": raw.get("translation_x", 0.0),
            "translation_y": raw.get("translation_y", 0.0),
            "translation_z": raw.get("translation_z", 0.0),
            "rotation_x":    raw.get("rotation_x", 0.0),
            "rotation_y":    raw.get("rotation_y", 0.0),
            "rotation_z":    raw.get("rotation_z", 0.0),
            "scale_x":       raw.get("scale_x", 1.0),
            "scale_y":       raw.get("scale_y", 1.0),
            "scale_z":       raw.get("scale_z", 1.0),
        }

    if "I3D_Visual" in injected:
        interfaces["I3D_Visual"] = {
            "material_variant": raw.get("material_variant", "normal"),
            "is_visible": raw.get("is_visible", True)
        }

    if "I3D_Behavioral" in injected:
        interfaces["I3D_Behavioral"] = {
            "animation_state":  raw.get("animation_state", "idle"),
            "fx_trigger":       raw.get("fx_trigger", ""),
            "ui_label_content": raw.get("ui_label_content", instance_id)
        }

    return {
        "instanceId":      instance_id,
        "objectTypeRid":   ot_rid,
        "objectTypeName":  ot.get("name", ot_rid),
        "timestamp":       now,
        "online":          online,
        "raw_state":       raw,
        "interfaces":      interfaces,
        "injected_interfaces": injected
    }

@app.route('/api/v2/state/snapshot', methods=['GET'])
def get_state_snapshot():
    """获取指定实例经接口映射后的表现值快照"""
    instance_id = request.args.get('id')
    if not instance_id:
        return jsonify({"error": "Missing instance id"}), 400
    snap = _build_snapshot(instance_id)
    if snap is None:
        return jsonify({"error": "Instance not found"}), 404
    return jsonify(snap)

@app.route('/api/v2/state/snapshots', methods=['GET'])
def get_all_snapshots():
    """获取所有实例的快照（3D 渲染端批量轮询用）"""
    result = []
    for iid in instance_store.get_all_ids():
        snap = _build_snapshot(iid)
        if snap:
            result.append(snap)
    return jsonify(result)

@app.route('/api/v2/state/override', methods=['POST'])
def override_state():
    """
    手动 Override 指定实例的属性值（调试用）。
    Body: { "instance_id": str, "patch": { field: value, ... } }
    """
    data = request.json or {}
    instance_id = data.get("instance_id")
    patch = data.get("patch", {})
    if not instance_id:
        return jsonify({"error": "instance_id is required"}), 400

    # 类型转换：数值字段强制 float
    numeric_fields = {
        'translation_x', 'translation_y', 'translation_z',
        'rotation_x', 'rotation_y', 'rotation_z',
        'scale_x', 'scale_y', 'scale_z'
    }
    for k, v in patch.items():
        if k in numeric_fields:
            try:
                patch[k] = float(v)
            except (ValueError, TypeError):
                pass
        if k in ('is_visible', 'is_loaded') and isinstance(v, str):
            patch[k] = v.lower() not in ('false', '0', 'no')

    success = instance_store.update_raw_state(instance_id, patch)
    if not success:
        return jsonify({"error": "Instance not found"}), 404

    snap = _build_snapshot(instance_id)
    return jsonify({"status": "ok", "snapshot": snap})


# ═══════════════════════════════════════════════════════════════
# 旧版 2.x 映射规则 API（保留兼容）
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/mapping/rules', methods=['GET'])
def list_mapping_rules():
    return jsonify(mapping_store.list_rules())

@app.route('/api/v2/mapping/rules', methods=['POST'])
def save_mapping_rule():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    return jsonify(mapping_store.save_rule(data)), 201

@app.route('/api/v2/mapping/rules/<rule_id>', methods=['GET'])
def get_mapping_rule(rule_id):
    rule = mapping_store.get_rule(rule_id)
    if rule:
        return jsonify(rule)
    return jsonify({"error": "Rule not found"}), 404

@app.route('/api/v2/mapping/rules/<rule_id>', methods=['DELETE'])
def delete_mapping_rule(rule_id):
    if mapping_store.delete_rule(rule_id):
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Rule not found"}), 404


# ═══════════════════════════════════════════════════════════════
# 知识图谱 Mock 数据（ontology_graph.html 用）
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/ontology/graph_data', methods=['GET'])
def get_graph_data():
    nodes = [
        {
            "id": "Employee",
            "name": "工厂员工",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.employee",
            "api_name": "Employee",
            "display_name": "工厂员工",
            "description": "工厂员工",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Worker",
            "name": "一线作业人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.worker",
            "api_name": "Worker",
            "display_name": "一线作业人员",
            "description": "一线作业人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Manager",
            "name": "管理人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.manager",
            "api_name": "Manager",
            "display_name": "管理人员",
            "description": "管理人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "QualityInspector",
            "name": "质检人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.qualityinspector",
            "api_name": "QualityInspector",
            "display_name": "质检人员",
            "description": "质检人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "MaintenanceStaff",
            "name": "设备维保人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.maintenancestaff",
            "api_name": "MaintenanceStaff",
            "display_name": "设备维保人员",
            "description": "设备维保人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "WarehouseKeeper",
            "name": "仓储管理员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.warehousekeeper",
            "api_name": "WarehouseKeeper",
            "display_name": "仓储管理员",
            "description": "仓储管理员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Operator",
            "name": "设备操作工",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.operator",
            "api_name": "Operator",
            "display_name": "设备操作工",
            "description": "设备操作工",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Technician",
            "name": "技术人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.technician",
            "api_name": "Technician",
            "display_name": "技术人员",
            "description": "技术人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "SecurityGuard",
            "name": "安保人员",
            "category": "Personnel",
            "symbolSize": 30,
            "rid": "ri.obj.securityguard",
            "api_name": "SecurityGuard",
            "display_name": "安保人员",
            "description": "安保人员",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Equipment",
            "name": "生产设备",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.equipment",
            "api_name": "Equipment",
            "display_name": "生产设备",
            "description": "生产设备",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "MachineTool",
            "name": "机床",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.machinetool",
            "api_name": "MachineTool",
            "display_name": "机床",
            "description": "机床",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Robot",
            "name": "工业机器人",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.robot",
            "api_name": "Robot",
            "display_name": "工业机器人",
            "description": "工业机器人",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Conveyor",
            "name": "传送带",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.conveyor",
            "api_name": "Conveyor",
            "display_name": "传送带",
            "description": "传送带",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Forklift",
            "name": "叉车",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.forklift",
            "api_name": "Forklift",
            "display_name": "叉车",
            "description": "叉车",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "AGV",
            "name": "自动导引车",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.agv",
            "api_name": "AGV",
            "display_name": "自动导引车",
            "description": "自动导引车",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Cart",
            "name": "手推车",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.cart",
            "api_name": "Cart",
            "display_name": "手推车",
            "description": "手推车",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "PalletJack",
            "name": "地牛",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.palletjack",
            "api_name": "PalletJack",
            "display_name": "地牛",
            "description": "地牛",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Scanner",
            "name": "扫码设备",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.scanner",
            "api_name": "Scanner",
            "display_name": "扫码设备",
            "description": "扫码设备",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "IndustrialScale",
            "name": "地磅",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.industrialscale",
            "api_name": "IndustrialScale",
            "display_name": "地磅",
            "description": "地磅",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ProductionTool",
            "name": "工装工具",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.productiontool",
            "api_name": "ProductionTool",
            "display_name": "工装工具",
            "description": "工装工具",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Fixture",
            "name": "夹具",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.fixture",
            "api_name": "Fixture",
            "display_name": "夹具",
            "description": "夹具",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Mold",
            "name": "模具",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.mold",
            "api_name": "Mold",
            "display_name": "模具",
            "description": "模具",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "QualityInstrument",
            "name": "质检仪器",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.qualityinstrument",
            "api_name": "QualityInstrument",
            "display_name": "质检仪器",
            "description": "质检仪器",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Rack",
            "name": "仓储货架",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.rack",
            "api_name": "Rack",
            "display_name": "仓储货架",
            "description": "仓储货架",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Table",
            "name": "工作台",
            "category": "Machine",
            "symbolSize": 35,
            "rid": "ri.obj.table",
            "api_name": "Table",
            "display_name": "工作台",
            "description": "工作台",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "RawMaterial",
            "name": "原材料",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.rawmaterial",
            "api_name": "RawMaterial",
            "display_name": "原材料",
            "description": "原材料",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "SemiFinishedGood",
            "name": "半成品",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.semifinishedgood",
            "api_name": "SemiFinishedGood",
            "display_name": "半成品",
            "description": "半成品",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "FinishedGood",
            "name": "成品",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.finishedgood",
            "api_name": "FinishedGood",
            "display_name": "成品",
            "description": "成品",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Material",
            "name": "通用物料",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.material",
            "api_name": "Material",
            "display_name": "通用物料",
            "description": "通用物料",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Box",
            "name": "包装箱",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.box",
            "api_name": "Box",
            "display_name": "包装箱",
            "description": "包装箱",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Bag",
            "name": "袋装物料",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.bag",
            "api_name": "Bag",
            "display_name": "袋装物料",
            "description": "袋装物料",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Barrel",
            "name": "桶装物料",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.barrel",
            "api_name": "Barrel",
            "display_name": "桶装物料",
            "description": "桶装物料",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Pallet",
            "name": "托盘",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.pallet",
            "api_name": "Pallet",
            "display_name": "托盘",
            "description": "托盘",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "CableDrum",
            "name": "电缆盘",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.cabledrum",
            "api_name": "CableDrum",
            "display_name": "电缆盘",
            "description": "电缆盘",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ShippingCrate",
            "name": "木箱",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.shippingcrate",
            "api_name": "ShippingCrate",
            "display_name": "木箱",
            "description": "木箱",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "MaterialBatch",
            "name": "物料批次",
            "category": "Material",
            "symbolSize": 30,
            "rid": "ri.obj.materialbatch",
            "api_name": "MaterialBatch",
            "display_name": "物料批次",
            "description": "物料批次",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Workstation",
            "name": "工位",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.workstation",
            "api_name": "Workstation",
            "display_name": "工位",
            "description": "工位",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ProductionLine",
            "name": "生产线",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.productionline",
            "api_name": "ProductionLine",
            "display_name": "生产线",
            "description": "生产线",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Process",
            "name": "生产工艺",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.process",
            "api_name": "Process",
            "display_name": "生产工艺",
            "description": "生产工艺",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "WorkInstruction",
            "name": "作业指导书",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.workinstruction",
            "api_name": "WorkInstruction",
            "display_name": "作业指导书",
            "description": "作业指导书",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ProcessParameter",
            "name": "工艺参数",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.processparameter",
            "api_name": "ProcessParameter",
            "display_name": "工艺参数",
            "description": "工艺参数",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ProductionPlan",
            "name": "生产计划",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.productionplan",
            "api_name": "ProductionPlan",
            "display_name": "生产计划",
            "description": "生产计划",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "QualityStandard",
            "name": "质量标准",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.qualitystandard",
            "api_name": "QualityStandard",
            "display_name": "质量标准",
            "description": "质量标准",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "SafetyRule",
            "name": "安全规范",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.safetyrule",
            "api_name": "SafetyRule",
            "display_name": "安全规范",
            "description": "安全规范",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "MaintenancePlan",
            "name": "维保计划",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.maintenanceplan",
            "api_name": "MaintenancePlan",
            "display_name": "维保计划",
            "description": "维保计划",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "SOP",
            "name": "标准作业程序",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.sop",
            "api_name": "SOP",
            "display_name": "标准作业程序",
            "description": "标准作业程序",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "InspectionRule",
            "name": "检验规范",
            "category": "Method",
            "symbolSize": 35,
            "rid": "ri.obj.inspectionrule",
            "api_name": "InspectionRule",
            "display_name": "检验规范",
            "description": "检验规范",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Wall",
            "name": "墙体",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.wall",
            "api_name": "Wall",
            "display_name": "墙体",
            "description": "墙体",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Floor",
            "name": "地面",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.floor",
            "api_name": "Floor",
            "display_name": "地面",
            "description": "地面",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Ceiling",
            "name": "吊顶",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.ceiling",
            "api_name": "Ceiling",
            "display_name": "吊顶",
            "description": "吊顶",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Door",
            "name": "门",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.door",
            "api_name": "Door",
            "display_name": "门",
            "description": "门",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Window",
            "name": "窗",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.window",
            "api_name": "Window",
            "display_name": "窗",
            "description": "窗",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Workshop",
            "name": "车间",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.workshop",
            "api_name": "Workshop",
            "display_name": "车间",
            "description": "车间",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Warehouse",
            "name": "仓库",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.warehouse",
            "api_name": "Warehouse",
            "display_name": "仓库",
            "description": "仓库",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "OfficeArea",
            "name": "办公区",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.officearea",
            "api_name": "OfficeArea",
            "display_name": "办公区",
            "description": "办公区",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "LoadingDock",
            "name": "装卸区",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.loadingdock",
            "api_name": "LoadingDock",
            "display_name": "装卸区",
            "description": "装卸区",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Pipe",
            "name": "管道",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.pipe",
            "api_name": "Pipe",
            "display_name": "管道",
            "description": "管道",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "AirDuct",
            "name": "通风管道",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.airduct",
            "api_name": "AirDuct",
            "display_name": "通风管道",
            "description": "通风管道",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "CableTray",
            "name": "电缆桥架",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.cabletray",
            "api_name": "CableTray",
            "display_name": "电缆桥架",
            "description": "电缆桥架",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "Lamp",
            "name": "照明灯具",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.lamp",
            "api_name": "Lamp",
            "display_name": "照明灯具",
            "description": "照明灯具",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "FireExtinguisher",
            "name": "灭火器",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.fireextinguisher",
            "api_name": "FireExtinguisher",
            "display_name": "灭火器",
            "description": "灭火器",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "FireAlarm",
            "name": "火警报警器",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.firealarm",
            "api_name": "FireAlarm",
            "display_name": "火警报警器",
            "description": "火警报警器",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "FirstAidKit",
            "name": "急救箱",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.firstaidkit",
            "api_name": "FirstAidKit",
            "display_name": "急救箱",
            "description": "急救箱",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "SafetyFacility",
            "name": "安全防护设施",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.safetyfacility",
            "api_name": "SafetyFacility",
            "display_name": "安全防护设施",
            "description": "安全防护设施",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "EnvironmentalDevice",
            "name": "环境设备",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.environmentaldevice",
            "api_name": "EnvironmentalDevice",
            "display_name": "环境设备",
            "description": "环境设备",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "ColumnGuard",
            "name": "防撞柱",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.columnguard",
            "api_name": "ColumnGuard",
            "display_name": "防撞柱",
            "description": "防撞柱",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "GuardRail",
            "name": "护栏",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.guardrail",
            "api_name": "GuardRail",
            "display_name": "护栏",
            "description": "护栏",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        },
        {
            "id": "EnvironmentalMonitor",
            "name": "环境监测设备",
            "category": "Environment",
            "symbolSize": 30,
            "rid": "ri.obj.environmentalmonitor",
            "api_name": "EnvironmentalMonitor",
            "display_name": "环境监测设备",
            "description": "环境监测设备",
            "lifecycle_status": "ACTIVE",
            "primary_keys": [
                "id"
            ]
        }
    ]
    links = [
        {
            "source": "Manager",
            "target": "ProductionPlan",
            "label": "develops"
        },
        {
            "source": "Manager",
            "target": "QualityStandard",
            "label": "approves"
        },
        {
            "source": "QualityInspector",
            "target": "QualityStandard",
            "label": "enforces"
        },
        {
            "source": "QualityInspector",
            "target": "QualityInstrument",
            "label": "uses"
        },
        {
            "source": "MaintenanceStaff",
            "target": "MaintenancePlan",
            "label": "executes"
        },
        {
            "source": "MaintenanceStaff",
            "target": "Robot",
            "label": "maintains"
        },
        {
            "source": "MaintenanceStaff",
            "target": "MachineTool",
            "label": "maintains"
        },
        {
            "source": "WarehouseKeeper",
            "target": "Warehouse",
            "label": "manages"
        },
        {
            "source": "WarehouseKeeper",
            "target": "MaterialBatch",
            "label": "tracks"
        },
        {
            "source": "WarehouseKeeper",
            "target": "Forklift",
            "label": "drives"
        },
        {
            "source": "Operator",
            "target": "MachineTool",
            "label": "operates"
        },
        {
            "source": "Operator",
            "target": "WorkInstruction",
            "label": "follows"
        },
        {
            "source": "SecurityGuard",
            "target": "SafetyRule",
            "label": "enforces"
        },
        {
            "source": "Technician",
            "target": "ProcessParameter",
            "label": "tunes"
        },
        {
            "source": "MachineTool",
            "target": "RawMaterial",
            "label": "processes"
        },
        {
            "source": "MachineTool",
            "target": "ProcessParameter",
            "label": "configured_by"
        },
        {
            "source": "Robot",
            "target": "SemiFinishedGood",
            "label": "assembles"
        },
        {
            "source": "Conveyor",
            "target": "SemiFinishedGood",
            "label": "moves"
        },
        {
            "source": "AGV",
            "target": "MaterialBatch",
            "label": "transports"
        },
        {
            "source": "AGV",
            "target": "Rack",
            "label": "docks_at"
        },
        {
            "source": "Scanner",
            "target": "MaterialBatch",
            "label": "scans"
        },
        {
            "source": "IndustrialScale",
            "target": "MaterialBatch",
            "label": "weighs"
        },
        {
            "source": "ProductionTool",
            "target": "Workstation",
            "label": "used_at"
        },
        {
            "source": "Fixture",
            "target": "MachineTool",
            "label": "mounted_on"
        },
        {
            "source": "RawMaterial",
            "target": "SemiFinishedGood",
            "label": "converted_to"
        },
        {
            "source": "SemiFinishedGood",
            "target": "FinishedGood",
            "label": "assembled_into"
        },
        {
            "source": "MaterialBatch",
            "target": "Box",
            "label": "packaged_in"
        },
        {
            "source": "Box",
            "target": "Pallet",
            "label": "stacked_on"
        },
        {
            "source": "Pallet",
            "target": "Rack",
            "label": "stored_in"
        },
        {
            "source": "ProductionPlan",
            "target": "ProductionLine",
            "label": "schedules"
        },
        {
            "source": "SOP",
            "target": "Process",
            "label": "standardizes"
        },
        {
            "source": "MaintenancePlan",
            "target": "Equipment",
            "label": "applies_to"
        },
        {
            "source": "InspectionRule",
            "target": "QualityInstrument",
            "label": "guides"
        },
        {
            "source": "SafetyRule",
            "target": "Workshop",
            "label": "applies_in"
        },
        {
            "source": "Workshop",
            "target": "ProductionLine",
            "label": "contains"
        },
        {
            "source": "Warehouse",
            "target": "Rack",
            "label": "contains"
        },
        {
            "source": "LoadingDock",
            "target": "AGV",
            "label": "serves"
        },
        {
            "source": "Wall",
            "target": "Workshop",
            "label": "structure_of"
        },
        {
            "source": "Floor",
            "target": "Workshop",
            "label": "structure_of"
        },
        {
            "source": "Ceiling",
            "target": "Workshop",
            "label": "structure_of"
        },
        {
            "source": "Door",
            "target": "Wall",
            "label": "installed_in"
        },
        {
            "source": "Window",
            "target": "Wall",
            "label": "installed_in"
        },
        {
            "source": "Pipe",
            "target": "Ceiling",
            "label": "hung_from"
        },
        {
            "source": "AirDuct",
            "target": "Ceiling",
            "label": "hung_from"
        },
        {
            "source": "CableTray",
            "target": "Ceiling",
            "label": "hung_from"
        },
        {
            "source": "Lamp",
            "target": "CableTray",
            "label": "draws_power"
        },
        {
            "source": "EnvironmentalMonitor",
            "target": "Lamp",
            "label": "co_located"
        },
        {
            "source": "FireExtinguisher",
            "target": "Wall",
            "label": "mounted_on"
        },
        {
            "source": "FireAlarm",
            "target": "Wall",
            "label": "mounted_on"
        },
        {
            "source": "FirstAidKit",
            "target": "Wall",
            "label": "mounted_on"
        },
        {
            "source": "GuardRail",
            "target": "Floor",
            "label": "guards"
        },
        {
            "source": "ColumnGuard",
            "target": "Floor",
            "label": "protects"
        }
    ]
    categories = [
        {"name": "Personnel"}, {"name": "Machine"}, {"name": "Material"},
        {"name": "Method"}, {"name": "Environment"}
    ]
    
    # 动态同步对象类型中已注入的三维能力接口
    for node in nodes:
        rid = node.get("rid")
        if rid and rid in _object_types:
            node["interfaces"] = _object_types[rid].get("injected_interfaces", [])
            
    return jsonify({"nodes": nodes, "links": links, "categories": categories})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
