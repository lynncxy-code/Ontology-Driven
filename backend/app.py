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
            "is_visible": raw.get("is_visible", True)
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
            "material_variant": raw.get("material_variant", "normal")
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
        if k == 'is_visible' and isinstance(v, str):
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
            "id": "Aircraft", "name": "设备000125", "category": "Core", "symbolSize": 55,
            "rid": "ri.obj.airplane", "api_name": "Aircraft", "display_name": "设备000125",
            "description": "大型民用客机设备实体，具备完整飞行数据与状态接口",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Behavioral"],
            "primary_keys": ["serial_number"],
            "read_conn_id": "conn.mqtt.c919", "read_path": "/topics/aircraft/+/telemetry",
            "writeback_enabled": False
        },
        {
            "id": "Engine", "name": "CFM LEAP-1C 发动机", "category": "Part", "symbolSize": 40,
            "rid": "ri.obj.engine", "api_name": "Engine", "display_name": "CFM LEAP-1C 发动机",
            "description": "C919主动力装置，双发涡扇发动机",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial"],
            "primary_keys": ["serial_number"],
            "read_conn_id": "conn.opcua.engine", "read_path": "ns=2;s=Engine.RPM",
            "writeback_enabled": False
        },
        {
            "id": "Wing", "name": "超临界机翼", "category": "Part", "symbolSize": 40,
            "rid": "ri.obj.wing", "api_name": "Wing", "display_name": "超临界机翼",
            "description": "采用超临界翼型设计，碳纤维复合材料结构",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
            "primary_keys": ["component_id"],
            "read_conn_id": None, "read_path": None,
            "writeback_enabled": False
        },
        {
            "id": "LandingGear", "name": "主起落架", "category": "Part", "symbolSize": 40,
            "rid": "ri.obj.landing_gear", "api_name": "LandingGear", "display_name": "主起落架",
            "description": "主起落架组件，含液压收放系统",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Behavioral"],
            "primary_keys": ["component_id"],
            "read_conn_id": "conn.opcua.lgr", "read_path": "ns=2;s=LandingGear.Status",
            "writeback_enabled": True,
            "write_conn_id": "conn.opcua.lgr", "write_path": "ns=2;s=LandingGear.Override"
        },
        {
            "id": "AGV", "name": "自动导引车 (AGV)", "category": "Machine", "symbolSize": 35,
            "rid": "ri.obj.agv", "api_name": "AGV", "display_name": "自动导引车 (AGV)",
            "description": "用于物料搬运和装配支援的自动引导车辆",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Behavioral"],
            "primary_keys": ["serial_number"],
            "read_conn_id": "conn.mqtt.agv", "read_path": "/agv/+/status",
            "writeback_enabled": True,
            "write_conn_id": "conn.mqtt.agv", "write_path": "/agv/+/command"
        },
        {
            "id": "AssemblyJig", "name": "翼身对接型架", "category": "Tooling", "symbolSize": 30,
            "rid": "ri.obj.tooling", "api_name": "AssemblyJig", "display_name": "翼身对接工装",
            "description": "飞机翼身对接用精密型架，含液压定位系统",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial"],
            "primary_keys": ["serial_number"],
            "read_conn_id": "conn.plc.jig01", "read_path": "%DB10.DBD0",
            "writeback_enabled": False
        },
        {
            "id": "Mechanic", "name": "王工程师", "category": "Personnel", "symbolSize": 40,
            "rid": "ri.obj.personnel", "api_name": "Mechanic", "display_name": "王工程师",
            "description": "高级装配技师，持有航空维修执照",
            "lifecycle_status": "ACTIVE",
            "interfaces": [],
            "primary_keys": ["employee_id"],
            "read_conn_id": None, "read_path": None,
            "writeback_enabled": False
        },
        {
            "id": "CompositeMat", "name": "T800 碳纤维", "category": "Material", "symbolSize": 30,
            "rid": "ri.obj.material", "api_name": "CompositeMat", "display_name": "T800 碳纤维",
            "description": "高强度碳纤维复合材料，用于机翼蒙皮结构",
            "lifecycle_status": "ACTIVE",
            "interfaces": [],
            "primary_keys": ["batch_number"],
            "read_conn_id": "conn.erp.mes", "read_path": "/materials/carbon/T800",
            "writeback_enabled": False
        },
        {
            "id": "SOP_Wing", "name": "机翼装配 SOP", "category": "Method", "symbolSize": 25,
            "rid": "ri.obj.sop", "api_name": "SOP_Wing", "display_name": "机翼装配作业规程",
            "description": "机翼总装作业标准规程，修订版 Rev.3",
            "lifecycle_status": "ACTIVE",
            "interfaces": [],
            "primary_keys": ["doc_id"],
            "read_conn_id": None, "read_path": None,
            "writeback_enabled": False
        },
        {
            "id": "WorkshopEnv", "name": "101 号总装厂房", "category": "Environment", "symbolSize": 25,
            "rid": "ri.obj.environment", "api_name": "WorkshopEnv", "display_name": "101号总装厂房",
            "description": "大型总装集成厂房，恒温恒湿洁净环境",
            "lifecycle_status": "ACTIVE",
            "interfaces": [],
            "primary_keys": ["building_id"],
            "read_conn_id": "conn.iot.bms", "read_path": "/buildings/101/env",
            "writeback_enabled": False
        },
        {
            "id": "AssemblyLine", "name": "脉动总装生产线", "category": "Line", "symbolSize": 50,
            "rid": "ri.obj.assembly_line", "api_name": "AssemblyLine", "display_name": "脉动总装生产线",
            "description": "C919脉动式总装生产线，共6个站位",
            "lifecycle_status": "ACTIVE",
            "interfaces": ["I3D_Representable", "I3D_Spatial"],
            "primary_keys": ["line_id"],
            "read_conn_id": "conn.mes.line", "read_path": "/lines/c919/stations",
            "writeback_enabled": True,
            "write_conn_id": "conn.mes.line", "write_path": "/lines/c919/dispatch"
        },
        {
            "id": "Event_Alert", "name": "液压系统压力告警", "category": "Event", "symbolSize": 30,
            "rid": "ri.obj.event", "api_name": "Event_Alert", "display_name": "液压系统压力告警",
            "description": "主起落架液压管路压力超限事件，告警等级 Level-2",
            "lifecycle_status": "DRAFT",
            "interfaces": [],
            "primary_keys": ["event_id"],
            "validation": {"pressure_threshold_kpa": 350, "alert_level": "Level-2"},
            "read_conn_id": None, "read_path": None,
            "writeback_enabled": False
        },
    ]
    links = [
        {"source": "Aircraft",    "target": "Engine",       "label": "has_part"},
        {"source": "Aircraft",    "target": "Wing",         "label": "has_part"},
        {"source": "Aircraft",    "target": "LandingGear",  "label": "has_part"},
        {"source": "AGV",         "target": "Wing",         "label": "transports"},
        {"source": "AssemblyJig", "target": "Aircraft",     "label": "supports"},
        {"source": "Mechanic",    "target": "Engine",       "label": "installs"},
        {"source": "CompositeMat","target": "Wing",         "label": "used_in"},
        {"source": "SOP_Wing",    "target": "Wing",         "label": "guides_assembly"},
        {"source": "WorkshopEnv", "target": "AssemblyLine", "label": "surrounds"},
        {"source": "AssemblyLine","target": "Aircraft",     "label": "processes"},
        {"source": "Event_Alert", "target": "LandingGear",  "label": "occurred_on"},
    ]
    categories = [
        {"name": "Core"}, {"name": "Part"}, {"name": "Personnel"},
        {"name": "Machine"}, {"name": "Material"}, {"name": "Method"},
        {"name": "Environment"}, {"name": "Tooling"}, {"name": "Line"}, {"name": "Event"}
    ]
    
    # 动态同步对象类型中已注入的三维能力接口
    for node in nodes:
        rid = node.get("rid")
        if rid and rid in _object_types:
            node["interfaces"] = _object_types[rid].get("injected_interfaces", [])
            
    return jsonify({"nodes": nodes, "links": links, "categories": categories})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
