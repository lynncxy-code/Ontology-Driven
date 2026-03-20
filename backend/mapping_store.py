"""
映射规则存储 & 系统数据定义 (v2.3)

- OBJECT_TYPES: 本体对象类型注册表（含接口挂载状态）
- INTERFACES: 两层接口规范（I3D_Representable + 3 子能力）
- InstanceStore: 动态实例内存管理
- MockInstanceSimulator: 后台数据模拟线程
"""

import json
import os
import time
import uuid
import threading
import random
import math

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "mapping_rules.json")


class MappingStore:
    def __init__(self, filepath=None):
        self.filepath = filepath or _DEFAULT_PATH
        self.rules = {}
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.rules = {r["id"]: r for r in data if "id" in r}
                else:
                    self.rules = data
        else:
            self.rules = {}

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, ensure_ascii=False, indent=2)

    def list_rules(self):
        return list(self.rules.values())

    def get_rule(self, rule_id):
        return self.rules.get(rule_id)

    def save_rule(self, rule_data):
        if "id" not in rule_data or not rule_data["id"]:
            rule_data["id"] = str(uuid.uuid4())[:8]
        rule_data["updated_at"] = time.time()
        self.rules[rule_data["id"]] = rule_data
        self._save()
        return rule_data

    def delete_rule(self, rule_id):
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save()
            return True
        return False


# ═══════════════════════════════════════════════════════════════
# 接口规范 V1.1 — 两层结构
# I3D_Representable（顶层·必选）+ 3 个子能力（可选）
# ═══════════════════════════════════════════════════════════════

INTERFACES = [
    {
        "rid": "I3D_Representable",
        "label": "三维存在接口",
        "tier": "parent",
        "required": True,
        "description": "声明该对象具备在三维场景中存在的能力，是所有子接口的前提。",
        "properties": [
            {"name": "asset_id",    "label": "资产唯一码 (GLB)", "type": "string"},
            {"name": "is_visible",  "label": "是否渲染",         "type": "boolean"}
        ]
    },
    {
        "rid": "I3D_Spatial",
        "label": "空间变换接口",
        "tier": "child",
        "required": False,
        "description": "赋予对象在三维空间中定位、旋转、缩放的能力（坐标单位：cm，现实 1:1）。",
        "properties": [
            {"name": "translation_x", "label": "位置 X (cm)", "type": "number", "default": 0.0},
            {"name": "translation_y", "label": "位置 Y (cm)", "type": "number", "default": 0.0},
            {"name": "translation_z", "label": "位置 Z (cm)", "type": "number", "default": 0.0},
            {"name": "rotation_x",    "label": "旋转 X (°)",  "type": "number", "default": 0.0},
            {"name": "rotation_y",    "label": "旋转 Y (°)",  "type": "number", "default": 0.0},
            {"name": "rotation_z",    "label": "旋转 Z (°)",  "type": "number", "default": 0.0},
            {"name": "scale_x",       "label": "缩放 X",      "type": "number", "default": 1.0},
            {"name": "scale_y",       "label": "缩放 Y",      "type": "number", "default": 1.0},
            {"name": "scale_z",       "label": "缩放 Z",      "type": "number", "default": 1.0}
        ]
    },
    {
        "rid": "I3D_Visual",
        "label": "视觉表达接口",
        "tier": "child",
        "required": False,
        "description": "赋予对象切换材质外观的能力。资产加载与整体显隐由 I3D_Representable 管理。",
        "properties": [
            {"name": "material_variant", "label": "材质变体", "type": "enum",
             "options": ["normal", "alarm", "offline", "highlight"], "default": "normal"}
        ]
    },
    {
        "rid": "I3D_Behavioral",
        "label": "动态行为接口",
        "tier": "child",
        "required": False,
        "description": "赋予对象执行动态行为与信息标注的能力。",
        "properties": [
            {"name": "animation_state",  "label": "动画状态",  "type": "string", "default": "idle"},
            {"name": "fx_trigger",       "label": "特效触发",  "type": "string", "default": ""},
            {"name": "ui_label_content", "label": "标签内容",  "type": "string", "default": ""}
        ]
    }
]

INTERFACE_MAP = {i["rid"]: i for i in INTERFACES}


# ═══════════════════════════════════════════════════════════════
# 本体对象类型注册表 (ObjectType Registry)
# ═══════════════════════════════════════════════════════════════

OBJECT_TYPES = {
    "ri.obj.airplane": {
        "rid": "ri.obj.airplane",
        "name": "设备000125",
        "category": "Core",
        "description": "大型民用客机设备实体，具备完整飞行数据与状态接口",
        "color": "#60a5fa",
        "properties": [
            {"name": "serial_number",    "label": "设备序列号 (Serial No.)",           "type": "string"},
            {"name": "model",            "label": "型号规格 (Model)",                   "type": "string"},
            {"name": "altitude",         "label": "飞行高度 (Altitude / m)",            "type": "number"},
            {"name": "speed",            "label": "飞行速度 (Speed / km·h⁻¹)",          "type": "number"},
            {"name": "heading",          "label": "航向角 (Heading / °)",               "type": "number"},
            {"name": "fuel_level",       "label": "燃油余量 (Fuel Level / %)",          "type": "number"},
            {"name": "engine_rpm",       "label": "发动机转速 (Engine RPM)",            "type": "number"},
            {"name": "cabin_pressure",   "label": "舱内气压 (Cabin Pressure / hPa)",    "type": "number"},
            {"name": "status",           "label": "运行状态 (Status)",                  "type": "enum",
             "options": ["normal", "warning", "fault", "offline"]},
            {"name": "maintenance_due",  "label": "下次维护日期 (Maintenance Due)",     "type": "string"},
        ],
        "injected_interfaces": [],
        "mock_instances": ["B-919A", "B-919B"],
        "asset_id": None
    },
    "ri.obj.agv": {
        "rid": "ri.obj.agv",
        "name": "自动导引车 (AGV)",
        "category": "Machine",
        "description": "用于物料搬运和装配支援的自引导车辆",
        "color": "#34d399",
        "properties": [
            {"name": "serial_number",    "label": "设备序列号 (Serial No.)",            "type": "string"},
            {"name": "battery_level",    "label": "电量 (Battery / %)",                 "type": "number"},
            {"name": "speed",            "label": "移动速度 (Speed / m·s⁻¹)",           "type": "number"},
            {"name": "position_x",       "label": "当前位置 X (Position X / cm)",       "type": "number"},
            {"name": "position_y",       "label": "当前位置 Y (Position Y / cm)",       "type": "number"},
            {"name": "load_weight",      "label": "当前载重 (Load / kg)",               "type": "number"},
            {"name": "max_load",         "label": "额定载重 (Max Load / kg)",           "type": "number"},
            {"name": "task_id",          "label": "当前任务 ID (Task ID)",              "type": "string"},
            {"name": "status",           "label": "运行状态 (Status)",                  "type": "enum",
             "options": ["idle", "running", "charging", "fault"]},
            {"name": "error_code",       "label": "故障码 (Error Code)",               "type": "string"},
        ],
        "injected_interfaces": [],
        "mock_instances": ["AGV-101", "AGV-102", "AGV-103"],
        "asset_id": None
    },
    "ri.obj.tooling": {
        "rid": "ri.obj.tooling",
        "name": "翼身对接工装",
        "category": "Tooling",
        "description": "飞机翼身对接用精密型架",
        "color": "#f59e0b",
        "properties": [
            {"name": "serial_number",    "label": "工装序列号 (Serial No.)",            "type": "string"},
            {"name": "jig_type",         "label": "型架类型 (Jig Type)",               "type": "string"},
            {"name": "temperature",      "label": "环境温度 (Temperature / °C)",        "type": "number"},
            {"name": "pressure",         "label": "液压压力 (Pressure / kPa)",          "type": "number"},
            {"name": "clamping_force",   "label": "夹紧力 (Clamping Force / kN)",       "type": "number"},
            {"name": "calibration_date", "label": "上次校准日期 (Calibration Date)",    "type": "string"},
            {"name": "accuracy",         "label": "定位精度 (Accuracy / mm)",           "type": "number"},
            {"name": "max_load",         "label": "额定承重 (Max Load / T)",            "type": "number"},
            {"name": "status",           "label": "工装状态 (Status)",                  "type": "enum",
             "options": ["available", "in_use", "maintenance"]},
            {"name": "operator_id",      "label": "操作员工号 (Operator ID)",          "type": "string"},
        ],
        "injected_interfaces": [],
        "mock_instances": ["JIG-W01", "JIG-W02"],
        "asset_id": None
    }
}


# ═══════════════════════════════════════════════════════════════
# 资产库 Mock（模拟 GLB 资产元数据）
# ═══════════════════════════════════════════════════════════════

MOCK_ASSETS = {
    # ── 原始 Mock 资产（保留兼容） ───────────────────────────────────────
    "6D654-G3-9453": {
        "file_number": "6D654-G3-9453",
        "name": "标准型号客机 (C919)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Pallet_01a",
        "bounding_box": {"x": 3885, "y": 3580, "z": 1230},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "AGV-001-STD": {
        "file_number": "AGV-001-STD",
        "name": "标准 AGV 小车",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Pallet_Truck_01a",
        "bounding_box": {"x": 200, "y": 120, "z": 80},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Behavioral"],
        "download_url": ""
    },
    "TOOL-JIG-001": {
        "file_number": "TOOL-JIG-001",
        "name": "翼身对接型架",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Industrial_Scale_01a",
        "bounding_box": {"x": 1500, "y": 800, "z": 600},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual", "I3D_Behavioral"],
        "download_url": ""
    },
    # ── UE 仓库资产包 (/Game/WarehouseProps_Bundle/Models/) ─────────────
    "SM_Rack_01a_Shelf": {
        "file_number": "SM_Rack_01a_Shelf",
        "name": "货架 (Shelf)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Rack_01a_Shelf",
        "bounding_box": {"x": 200, "y": 60, "z": 250},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Rack_01a_Top": {
        "file_number": "SM_Rack_01a_Top",
        "name": "货架顶部 (Rack Top)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Rack_01a_Top",
        "bounding_box": {"x": 200, "y": 60, "z": 10},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Table_01a": {
        "file_number": "SM_Table_01a",
        "name": "工作台 (Table)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Table_01a",
        "bounding_box": {"x": 150, "y": 80, "z": 75},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Pallet_01a": {
        "file_number": "SM_Pallet_01a",
        "name": "木托盘 (Pallet)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Pallet_01a",
        "bounding_box": {"x": 120, "y": 100, "z": 15},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Door_01": {
        "file_number": "SM_Door_01",
        "name": "仓库大门 (Door)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Door_01",
        "bounding_box": {"x": 200, "y": 20, "z": 300},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual", "I3D_Behavioral"],
        "download_url": ""
    },
    "SM_Factory_Floor_Flat": {
        "file_number": "SM_Factory_Floor_Flat",
        "name": "工厂地板 (Floor)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Factory_Floor_Flat",
        "bounding_box": {"x": 400, "y": 400, "z": 2},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Fire_Extinguisher_01": {
        "file_number": "SM_Fire_Extinguisher_01",
        "name": "灭火器 (Fire Extinguisher)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Fire_Extinguisher_01",
        "bounding_box": {"x": 15, "y": 15, "z": 50},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Shipping_Crate_01a": {
        "file_number": "SM_Shipping_Crate_01a",
        "name": "运输木箱 (Crate)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Shipping_Crate_01a",
        "bounding_box": {"x": 120, "y": 80, "z": 80},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Pole_01": {
        "file_number": "SM_Pole_01",
        "name": "立柱 (Pole)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Pole_01",
        "bounding_box": {"x": 10, "y": 10, "z": 300},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Lamp_01": {
        "file_number": "SM_Lamp_01",
        "name": "工业灯具 (Lamp)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Lamp_01",
        "bounding_box": {"x": 30, "y": 30, "z": 20},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Pipe_01a_10m": {
        "file_number": "SM_Pipe_01a_10m",
        "name": "金属管道 10m (Pipe)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Pipe_01a_10m",
        "bounding_box": {"x": 1000, "y": 10, "z": 10},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Mezzanine_01a_Beam": {
        "file_number": "SM_Mezzanine_01a_Beam",
        "name": "夹层横梁 (Beam)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Mezzanine_01a_Beam",
        "bounding_box": {"x": 500, "y": 20, "z": 20},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Reach_Truck_01a": {
        "file_number": "SM_Reach_Truck_01a",
        "name": "前移式叉车 (Reach Truck)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Reach_Truck_01a",
        "bounding_box": {"x": 250, "y": 100, "z": 220},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual", "I3D_Behavioral"],
        "download_url": ""
    },
    "SM_Scanner_01a": {
        "file_number": "SM_Scanner_01a",
        "name": "手持扫码枪 (Scanner)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Scanner_01a",
        "bounding_box": {"x": 20, "y": 8, "z": 15},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Medkit_01": {
        "file_number": "SM_Medkit_01",
        "name": "急救箱 (Medkit)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Medkit_01",
        "bounding_box": {"x": 30, "y": 20, "z": 25},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
}



# ═══════════════════════════════════════════════════════════════
# 动态实例存储 (InstanceStore)
# ═══════════════════════════════════════════════════════════════

class InstanceStore:
    """管理所有孪生体实例，支持动态投产与销毁。"""

    def __init__(self):
        self._lock = threading.Lock()
        # {instance_id: {id, object_type_rid, created_at, last_seen, status, raw_state}}
        self._instances = {}

    def spawn(self, instance_id, object_type_rid, initial_position=None):
        """创建新实例"""
        with self._lock:
            if initial_position is None:
                initial_position = {"x": 0.0, "y": 0.0, "z": 0.0}
            obj_type = OBJECT_TYPES.get(object_type_rid, {})
            # 初始 raw_state 根据 ObjectType 属性赋默认值
            raw_state = {
                "translation_x": float(initial_position.get("x", 0)),
                "translation_y": float(initial_position.get("y", 0)),
                "translation_z": float(initial_position.get("z", 0)),
                "rotation_x": 0.0, "rotation_y": 0.0, "rotation_z": 0.0,
                "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
                "material_variant": "normal",
                "animation_state": "idle",
                "fx_trigger": "",
                "ui_label_content": obj_type.get("name", instance_id),
                "status": "normal"
            }
            # 飞机特有属性
            if "airplane" in object_type_rid:
                raw_state.update({"altitude": 1000.0, "speed": 850.0, "heading": 0.0})
            elif "agv" in object_type_rid:
                raw_state.update({"battery_level": 85.0, "speed": 1.2})
            elif "tooling" in object_type_rid:
                raw_state.update({"temperature": 22.0, "pressure": 101.3})

            self._instances[instance_id] = {
                "id": instance_id,
                "object_type_rid": object_type_rid,
                "object_type_name": obj_type.get("name", object_type_rid),
                "created_at": time.time(),
                "last_seen": time.time(),
                "status": "online",
                "raw_state": raw_state
            }
        return self._instances[instance_id]

    def remove(self, instance_id):
        with self._lock:
            return self._instances.pop(instance_id, None)

    def list_all(self):
        with self._lock:
            now = time.time()
            result = []
            for iid, inst in self._instances.items():
                elapsed = now - inst["last_seen"]
                status = "online" if elapsed < 3.0 else "offline"
                result.append({
                    "id": iid,
                    "object_type_rid": inst["object_type_rid"],
                    "object_type_name": inst["object_type_name"],
                    "status": status,
                    "last_seen": inst["last_seen"],
                    "created_at": inst["created_at"]
                })
            return result

    def get_raw_state(self, instance_id):
        with self._lock:
            inst = self._instances.get(instance_id)
            if inst:
                return dict(inst["raw_state"])
            return None

    def update_raw_state(self, instance_id, patch):
        with self._lock:
            inst = self._instances.get(instance_id)
            if inst:
                inst["raw_state"].update(patch)
                inst["last_seen"] = time.time()
                return True
            return False

    def touch(self, instance_id):
        with self._lock:
            inst = self._instances.get(instance_id)
            if inst:
                inst["last_seen"] = time.time()

    def get_all_ids(self):
        with self._lock:
            return list(self._instances.keys())


# ═══════════════════════════════════════════════════════════════
# 后台模拟线程 (MockInstanceSimulator)
# ═══════════════════════════════════════════════════════════════

class MockInstanceSimulator(threading.Thread):
    """后台线程：定期更新所有实例的 raw_state，模拟传感数据波动。"""

    def __init__(self, instance_store: InstanceStore):
        super().__init__()
        self.daemon = True
        self.store = instance_store
        self._tick = 0

    def run(self):
        while True:
            time.sleep(1.0)
            self._tick += 1
            for iid in self.store.get_all_ids():
                state = self.store.get_raw_state(iid)
                if state is None:
                    continue
                patch = {}

                # 飞机：高度、速度、航向波动；坐标跟随高度
                if "plane" in iid or "airplane" in iid:
                    patch["altitude"] = max(0, state.get("altitude", 1000) + random.uniform(-20, 20))
                    patch["speed"]    = max(0, state.get("speed", 850) + random.uniform(-5, 5))
                    patch["heading"]  = (state.get("heading", 0) + random.uniform(-0.5, 0.5)) % 360
                    patch["translation_z"] = patch["altitude"]
                    patch["translation_x"] = state.get("translation_x", 0) + math.sin(self._tick * 0.05) * 2
                    patch["ui_label_content"] = f"高度 {patch['altitude']:.0f}m | 速度 {patch['speed']:.0f}km/h"
                    patch["animation_state"] = "flying"

                # AGV：电量缓慢消耗；位置移动
                elif "agv" in iid:
                    patch["battery_level"] = max(0, state.get("battery_level", 85) - 0.01)
                    patch["translation_x"] = state.get("translation_x", 0) + math.sin(self._tick * 0.1) * 5
                    patch["translation_y"] = state.get("translation_y", 0) + math.cos(self._tick * 0.1) * 3
                    patch["ui_label_content"] = f"电量 {patch['battery_level']:.1f}%"
                    patch["animation_state"] = "running" if patch["battery_level"] > 5 else "idle"

                # 工装：温度、压力波动
                elif "tool" in iid or "tooling" in iid:
                    patch["temperature"] = state.get("temperature", 22) + random.uniform(-0.2, 0.2)
                    patch["pressure"]    = state.get("pressure", 101) + random.uniform(-0.5, 0.5)
                    patch["ui_label_content"] = f"温度 {patch['temperature']:.1f}°C | 压力 {patch['pressure']:.1f}kPa"

                self.store.update_raw_state(iid, patch)


# ═══════════════════════════════════════════════════════════════
# 旧版兼容 (Ontology Properties & Transform Types)
# ═══════════════════════════════════════════════════════════════

ONTOLOGY_PROPERTIES = [
    {"name": "altitude",      "label": "高度 (Altitude)",   "type": "number"},
    {"name": "speed",         "label": "速度 (Speed)",      "type": "number"},
    {"name": "heading",       "label": "航向 (Heading)",    "type": "number"},
    {"name": "fuel_level",    "label": "油量 (Fuel)",       "type": "number"},
    {"name": "battery_level", "label": "电量 (Battery)",    "type": "number"},
    {"name": "temperature",   "label": "温度 (Temperature)","type": "number"},
    {"name": "pressure",      "label": "压力 (Pressure)",   "type": "number"},
    {"name": "status",        "label": "状态 (Status)",     "type": "enum",
     "options": ["normal", "warning", "fault", "offline"]},
]

TRANSFORM_TYPES = [
    {"type": "passthrough", "label": "直通 (Passthrough)", "description": "值直接传递"},
    {"type": "linear",      "label": "线性缩放 (Linear)",  "description": "y = scale * x + offset",
     "params": ["scale", "offset"]},
    {"type": "enum_map",    "label": "枚举映射 (Enum Map)","description": "值一对一映射",
     "params": ["map"]},
    {"type": "clamp",       "label": "范围限制 (Clamp)",   "description": "限制在 [min, max] 范围",
     "params": ["min", "max"]},
]
