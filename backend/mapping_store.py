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
             "options": ["normal", "wireframe", "gray", "highlight"], "default": "normal"}
        ]
    },
    {
        "rid": "I3D_Behavioral",
        "label": "动态行为接口",
        "tier": "child",
        "required": False,
        "description": "赋予对象执行动态行为与信息标注的能力。",
        "properties": [
            {"name": "animation_state",  "label": "动画状态",  "type": "enum", 
             "options": ["idle", "translate", "jump", "flip"], "default": "idle"},
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
    "ri.obj.employee": {
        "rid": "ri.obj.employee",
        "name": "Employee",
        "category": "Personnel",
        "description": "工厂员工",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Employee-001",
            "Employee-002"
        ],
        "asset_id": None
    },
    "ri.obj.worker": {
        "rid": "ri.obj.worker",
        "name": "Worker",
        "category": "Personnel",
        "description": "一线作业人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Worker-001",
            "Worker-002"
        ],
        "asset_id": None
    },
    "ri.obj.manager": {
        "rid": "ri.obj.manager",
        "name": "Manager",
        "category": "Personnel",
        "description": "管理人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Manager-001",
            "Manager-002"
        ],
        "asset_id": None
    },
    "ri.obj.qualityinspector": {
        "rid": "ri.obj.qualityinspector",
        "name": "QualityInspector",
        "category": "Personnel",
        "description": "质检人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "QualityInspector-001",
            "QualityInspector-002"
        ],
        "asset_id": None
    },
    "ri.obj.maintenancestaff": {
        "rid": "ri.obj.maintenancestaff",
        "name": "MaintenanceStaff",
        "category": "Personnel",
        "description": "设备维保人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "MaintenanceStaff-001",
            "MaintenanceStaff-002"
        ],
        "asset_id": None
    },
    "ri.obj.warehousekeeper": {
        "rid": "ri.obj.warehousekeeper",
        "name": "WarehouseKeeper",
        "category": "Personnel",
        "description": "仓储管理员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "WarehouseKeeper-001",
            "WarehouseKeeper-002"
        ],
        "asset_id": None
    },
    "ri.obj.operator": {
        "rid": "ri.obj.operator",
        "name": "Operator",
        "category": "Personnel",
        "description": "设备操作工",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Operator-001",
            "Operator-002"
        ],
        "asset_id": None
    },
    "ri.obj.technician": {
        "rid": "ri.obj.technician",
        "name": "Technician",
        "category": "Personnel",
        "description": "技术人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Technician-001",
            "Technician-002"
        ],
        "asset_id": None
    },
    "ri.obj.securityguard": {
        "rid": "ri.obj.securityguard",
        "name": "SecurityGuard",
        "category": "Personnel",
        "description": "安保人员",
        "color": "#f59e0b",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "SecurityGuard-001",
            "SecurityGuard-002"
        ],
        "asset_id": None
    },
    "ri.obj.equipment": {
        "rid": "ri.obj.equipment",
        "name": "Equipment",
        "category": "Machine",
        "description": "生产设备",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Equipment-001",
            "Equipment-002"
        ],
        "asset_id": None
    },
    "ri.obj.machinetool": {
        "rid": "ri.obj.machinetool",
        "name": "MachineTool",
        "category": "Machine",
        "description": "机床",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Behavioral"
        ],
        "mock_instances": [
            "MachineTool-001",
            "MachineTool-002",
            "MachineTool-003",
            "MachineTool-004",
            "MachineTool-005"
        ],
        "asset_id": None
    },
    "ri.obj.robot": {
        "rid": "ri.obj.robot",
        "name": "Robot",
        "category": "Machine",
        "description": "工业机器人",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Behavioral"
        ],
        "mock_instances": [
            "Robot-001",
            "Robot-002",
            "Robot-003",
            "Robot-004",
            "Robot-005",
            "Robot-006"
        ],
        "asset_id": None
    },
    "ri.obj.conveyor": {
        "rid": "ri.obj.conveyor",
        "name": "Conveyor",
        "category": "Machine",
        "description": "传送带",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Conveyor-001",
            "Conveyor-002"
        ],
        "asset_id": None
    },
    "ri.obj.forklift": {
        "rid": "ri.obj.forklift",
        "name": "Forklift",
        "category": "Machine",
        "description": "叉车",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Forklift-001",
            "Forklift-002"
        ],
        "asset_id": None
    },
    "ri.obj.agv": {
        "rid": "ri.obj.agv",
        "name": "AGV",
        "category": "Machine",
        "description": "自动导引车",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Behavioral"
        ],
        "mock_instances": [
            "AGV-001",
            "AGV-002",
            "AGV-003",
            "AGV-004",
            "AGV-005",
            "AGV-006",
            "AGV-007",
            "AGV-008"
        ],
        "asset_id": None
    },
    "ri.obj.cart": {
        "rid": "ri.obj.cart",
        "name": "Cart",
        "category": "Machine",
        "description": "手推车",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Cart-001",
            "Cart-002"
        ],
        "asset_id": None
    },
    "ri.obj.palletjack": {
        "rid": "ri.obj.palletjack",
        "name": "PalletJack",
        "category": "Machine",
        "description": "地牛",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "PalletJack-001",
            "PalletJack-002",
            "PalletJack-003",
            "PalletJack-004",
            "PalletJack-005",
            "PalletJack-006",
            "PalletJack-007"
        ],
        "asset_id": None
    },
    "ri.obj.scanner": {
        "rid": "ri.obj.scanner",
        "name": "Scanner",
        "category": "Machine",
        "description": "扫码设备",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Scanner-001",
            "Scanner-002"
        ],
        "asset_id": None
    },
    "ri.obj.industrialscale": {
        "rid": "ri.obj.industrialscale",
        "name": "IndustrialScale",
        "category": "Machine",
        "description": "地磅",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "IndustrialScale-001",
            "IndustrialScale-002"
        ],
        "asset_id": None
    },
    "ri.obj.productiontool": {
        "rid": "ri.obj.productiontool",
        "name": "ProductionTool",
        "category": "Machine",
        "description": "工装工具",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ProductionTool-001",
            "ProductionTool-002"
        ],
        "asset_id": None
    },
    "ri.obj.fixture": {
        "rid": "ri.obj.fixture",
        "name": "Fixture",
        "category": "Machine",
        "description": "夹具",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Fixture-001",
            "Fixture-002"
        ],
        "asset_id": None
    },
    "ri.obj.mold": {
        "rid": "ri.obj.mold",
        "name": "Mold",
        "category": "Machine",
        "description": "模具",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Mold-001",
            "Mold-002"
        ],
        "asset_id": None
    },
    "ri.obj.qualityinstrument": {
        "rid": "ri.obj.qualityinstrument",
        "name": "QualityInstrument",
        "category": "Machine",
        "description": "质检仪器",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "QualityInstrument-001",
            "QualityInstrument-002"
        ],
        "asset_id": None
    },
    "ri.obj.rack": {
        "rid": "ri.obj.rack",
        "name": "Rack",
        "category": "Machine",
        "description": "仓储货架",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Rack-001",
            "Rack-002"
        ],
        "asset_id": None
    },
    "ri.obj.table": {
        "rid": "ri.obj.table",
        "name": "Table",
        "category": "Machine",
        "description": "工作台",
        "color": "#3b82f6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Table-001",
            "Table-002"
        ],
        "asset_id": None
    },
    "ri.obj.rawmaterial": {
        "rid": "ri.obj.rawmaterial",
        "name": "RawMaterial",
        "category": "Material",
        "description": "原材料",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "RawMaterial-001",
            "RawMaterial-002"
        ],
        "asset_id": None
    },
    "ri.obj.semifinishedgood": {
        "rid": "ri.obj.semifinishedgood",
        "name": "SemiFinishedGood",
        "category": "Material",
        "description": "半成品",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "SemiFinishedGood-001",
            "SemiFinishedGood-002"
        ],
        "asset_id": None
    },
    "ri.obj.finishedgood": {
        "rid": "ri.obj.finishedgood",
        "name": "FinishedGood",
        "category": "Material",
        "description": "成品",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "FinishedGood-001",
            "FinishedGood-002"
        ],
        "asset_id": None
    },
    "ri.obj.material": {
        "rid": "ri.obj.material",
        "name": "Material",
        "category": "Material",
        "description": "通用物料",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Material-001",
            "Material-002"
        ],
        "asset_id": None
    },
    "ri.obj.box": {
        "rid": "ri.obj.box",
        "name": "Box",
        "category": "Material",
        "description": "包装箱",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Box-001",
            "Box-002"
        ],
        "asset_id": None
    },
    "ri.obj.bag": {
        "rid": "ri.obj.bag",
        "name": "Bag",
        "category": "Material",
        "description": "袋装物料",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Bag-001",
            "Bag-002"
        ],
        "asset_id": None
    },
    "ri.obj.barrel": {
        "rid": "ri.obj.barrel",
        "name": "Barrel",
        "category": "Material",
        "description": "桶装物料",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Barrel-001",
            "Barrel-002"
        ],
        "asset_id": None
    },
    "ri.obj.pallet": {
        "rid": "ri.obj.pallet",
        "name": "Pallet",
        "category": "Material",
        "description": "托盘",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Pallet-001",
            "Pallet-002"
        ],
        "asset_id": None
    },
    "ri.obj.cabledrum": {
        "rid": "ri.obj.cabledrum",
        "name": "CableDrum",
        "category": "Material",
        "description": "电缆盘",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "CableDrum-001",
            "CableDrum-002"
        ],
        "asset_id": None
    },
    "ri.obj.shippingcrate": {
        "rid": "ri.obj.shippingcrate",
        "name": "ShippingCrate",
        "category": "Material",
        "description": "木箱",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ShippingCrate-001",
            "ShippingCrate-002"
        ],
        "asset_id": None
    },
    "ri.obj.materialbatch": {
        "rid": "ri.obj.materialbatch",
        "name": "MaterialBatch",
        "category": "Material",
        "description": "物料批次",
        "color": "#8b5cf6",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "MaterialBatch-001",
            "MaterialBatch-002"
        ],
        "asset_id": None
    },
    "ri.obj.workstation": {
        "rid": "ri.obj.workstation",
        "name": "Workstation",
        "category": "Method",
        "description": "工位",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Workstation-001",
            "Workstation-002"
        ],
        "asset_id": None
    },
    "ri.obj.productionline": {
        "rid": "ri.obj.productionline",
        "name": "ProductionLine",
        "category": "Method",
        "description": "生产线",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ProductionLine-001",
            "ProductionLine-002"
        ],
        "asset_id": None
    },
    "ri.obj.process": {
        "rid": "ri.obj.process",
        "name": "Process",
        "category": "Method",
        "description": "生产工艺",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Process-001",
            "Process-002"
        ],
        "asset_id": None
    },
    "ri.obj.workinstruction": {
        "rid": "ri.obj.workinstruction",
        "name": "WorkInstruction",
        "category": "Method",
        "description": "作业指导书",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "WorkInstruction-001",
            "WorkInstruction-002"
        ],
        "asset_id": None
    },
    "ri.obj.processparameter": {
        "rid": "ri.obj.processparameter",
        "name": "ProcessParameter",
        "category": "Method",
        "description": "工艺参数",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ProcessParameter-001",
            "ProcessParameter-002"
        ],
        "asset_id": None
    },
    "ri.obj.productionplan": {
        "rid": "ri.obj.productionplan",
        "name": "ProductionPlan",
        "category": "Method",
        "description": "生产计划",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ProductionPlan-001",
            "ProductionPlan-002"
        ],
        "asset_id": None
    },
    "ri.obj.qualitystandard": {
        "rid": "ri.obj.qualitystandard",
        "name": "QualityStandard",
        "category": "Method",
        "description": "质量标准",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "QualityStandard-001",
            "QualityStandard-002"
        ],
        "asset_id": None
    },
    "ri.obj.safetyrule": {
        "rid": "ri.obj.safetyrule",
        "name": "SafetyRule",
        "category": "Method",
        "description": "安全规范",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "SafetyRule-001",
            "SafetyRule-002"
        ],
        "asset_id": None
    },
    "ri.obj.maintenanceplan": {
        "rid": "ri.obj.maintenanceplan",
        "name": "MaintenancePlan",
        "category": "Method",
        "description": "维保计划",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "MaintenancePlan-001",
            "MaintenancePlan-002"
        ],
        "asset_id": None
    },
    "ri.obj.sop": {
        "rid": "ri.obj.sop",
        "name": "SOP",
        "category": "Method",
        "description": "标准作业程序",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "SOP-001",
            "SOP-002"
        ],
        "asset_id": None
    },
    "ri.obj.inspectionrule": {
        "rid": "ri.obj.inspectionrule",
        "name": "InspectionRule",
        "category": "Method",
        "description": "检验规范",
        "color": "#ec4899",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "InspectionRule-001",
            "InspectionRule-002"
        ],
        "asset_id": None
    },
    "ri.obj.wall": {
        "rid": "ri.obj.wall",
        "name": "Wall",
        "category": "Environment",
        "description": "墙体",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Visual"
        ],
        "mock_instances": [
            "Wall-001",
            "Wall-002"
        ],
        "asset_id": None
    },
    "ri.obj.floor": {
        "rid": "ri.obj.floor",
        "name": "Floor",
        "category": "Environment",
        "description": "地面",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Visual"
        ],
        "mock_instances": [
            "Floor-001",
            "Floor-002"
        ],
        "asset_id": None
    },
    "ri.obj.ceiling": {
        "rid": "ri.obj.ceiling",
        "name": "Ceiling",
        "category": "Environment",
        "description": "吊顶",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Ceiling-001",
            "Ceiling-002"
        ],
        "asset_id": None
    },
    "ri.obj.door": {
        "rid": "ri.obj.door",
        "name": "Door",
        "category": "Environment",
        "description": "门",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Visual"
        ],
        "mock_instances": [
            "Door-001",
            "Door-002"
        ],
        "asset_id": None
    },
    "ri.obj.window": {
        "rid": "ri.obj.window",
        "name": "Window",
        "category": "Environment",
        "description": "窗",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Window-001",
            "Window-002"
        ],
        "asset_id": None
    },
    "ri.obj.workshop": {
        "rid": "ri.obj.workshop",
        "name": "Workshop",
        "category": "Environment",
        "description": "车间",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Workshop-001",
            "Workshop-002"
        ],
        "asset_id": None
    },
    "ri.obj.warehouse": {
        "rid": "ri.obj.warehouse",
        "name": "Warehouse",
        "category": "Environment",
        "description": "仓库",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Warehouse-001",
            "Warehouse-002"
        ],
        "asset_id": None
    },
    "ri.obj.officearea": {
        "rid": "ri.obj.officearea",
        "name": "OfficeArea",
        "category": "Environment",
        "description": "办公区",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "OfficeArea-001",
            "OfficeArea-002"
        ],
        "asset_id": None
    },
    "ri.obj.loadingdock": {
        "rid": "ri.obj.loadingdock",
        "name": "LoadingDock",
        "category": "Environment",
        "description": "装卸区",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "LoadingDock-001",
            "LoadingDock-002"
        ],
        "asset_id": None
    },
    "ri.obj.pipe": {
        "rid": "ri.obj.pipe",
        "name": "Pipe",
        "category": "Environment",
        "description": "管道",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "Pipe-001",
            "Pipe-002"
        ],
        "asset_id": None
    },
    "ri.obj.airduct": {
        "rid": "ri.obj.airduct",
        "name": "AirDuct",
        "category": "Environment",
        "description": "通风管道",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "AirDuct-001",
            "AirDuct-002"
        ],
        "asset_id": None
    },
    "ri.obj.cabletray": {
        "rid": "ri.obj.cabletray",
        "name": "CableTray",
        "category": "Environment",
        "description": "电缆桥架",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "CableTray-001",
            "CableTray-002"
        ],
        "asset_id": None
    },
    "ri.obj.lamp": {
        "rid": "ri.obj.lamp",
        "name": "Lamp",
        "category": "Environment",
        "description": "照明灯具",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Visual"
        ],
        "mock_instances": [
            "Lamp-001",
            "Lamp-002"
        ],
        "asset_id": None
    },
    "ri.obj.fireextinguisher": {
        "rid": "ri.obj.fireextinguisher",
        "name": "FireExtinguisher",
        "category": "Environment",
        "description": "灭火器",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [
            "I3D_Representable",
            "I3D_Spatial",
            "I3D_Visual"
        ],
        "mock_instances": [
            "FireExtinguisher-001",
            "FireExtinguisher-002"
        ],
        "asset_id": None
    },
    "ri.obj.firealarm": {
        "rid": "ri.obj.firealarm",
        "name": "FireAlarm",
        "category": "Environment",
        "description": "火警报警器",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "FireAlarm-001",
            "FireAlarm-002"
        ],
        "asset_id": None
    },
    "ri.obj.firstaidkit": {
        "rid": "ri.obj.firstaidkit",
        "name": "FirstAidKit",
        "category": "Environment",
        "description": "急救箱",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "FirstAidKit-001",
            "FirstAidKit-002"
        ],
        "asset_id": None
    },
    "ri.obj.safetyfacility": {
        "rid": "ri.obj.safetyfacility",
        "name": "SafetyFacility",
        "category": "Environment",
        "description": "安全防护设施",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "SafetyFacility-001",
            "SafetyFacility-002"
        ],
        "asset_id": None
    },
    "ri.obj.environmentaldevice": {
        "rid": "ri.obj.environmentaldevice",
        "name": "EnvironmentalDevice",
        "category": "Environment",
        "description": "环境设备",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "EnvironmentalDevice-001",
            "EnvironmentalDevice-002"
        ],
        "asset_id": None
    },
    "ri.obj.columnguard": {
        "rid": "ri.obj.columnguard",
        "name": "ColumnGuard",
        "category": "Environment",
        "description": "防撞柱",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "ColumnGuard-001",
            "ColumnGuard-002"
        ],
        "asset_id": None
    },
    "ri.obj.guardrail": {
        "rid": "ri.obj.guardrail",
        "name": "GuardRail",
        "category": "Environment",
        "description": "护栏",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "GuardRail-001",
            "GuardRail-002"
        ],
        "asset_id": None
    },
    "ri.obj.environmentalmonitor": {
        "rid": "ri.obj.environmentalmonitor",
        "name": "EnvironmentalMonitor",
        "category": "Environment",
        "description": "环境监测设备",
        "color": "#10b981",
        "properties": [
            {
                "name": "id",
                "label": "唯一标识",
                "type": "string"
            },
            {
                "name": "status",
                "label": "运行状态",
                "type": "enum",
                "options": [
                    "normal",
                    "warning",
                    "fault",
                    "offline"
                ]
            }
        ],
        "injected_interfaces": [],
        "mock_instances": [
            "EnvironmentalMonitor-001",
            "EnvironmentalMonitor-002"
        ],
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
    # ── 仓库 Props Bundle 扩展包（截图来源） ────────────────────────────
    "Assembly_line": {
        "file_number": "Assembly_line",
        "name": "装配线 (Assembly Line)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/Assembly_line",
        "bounding_box": {"x": 800, "y": 200, "z": 150},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual", "I3D_Behavioral"],
        "download_url": ""
    },
    "SM_Air_Duct_01_10m": {
        "file_number": "SM_Air_Duct_01_10m",
        "name": "通风管道 10m (Air Duct)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Air_Duct_01_10m",
        "bounding_box": {"x": 1000, "y": 40, "z": 40},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Air_Duct_01_1m": {
        "file_number": "SM_Air_Duct_01_1m",
        "name": "通风管道 1m (Air Duct)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Air_Duct_01_1m",
        "bounding_box": {"x": 100, "y": 40, "z": 40},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Air_Duct_01_2m": {
        "file_number": "SM_Air_Duct_01_2m",
        "name": "通风管道 2m (Air Duct)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Air_Duct_01_2m",
        "bounding_box": {"x": 200, "y": 40, "z": 40},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Air_Duct_01_5m": {
        "file_number": "SM_Air_Duct_01_5m",
        "name": "通风管道 5m (Air Duct)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Air_Duct_01_5m",
        "bounding_box": {"x": 500, "y": 40, "z": 40},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Bag_01a": {
        "file_number": "SM_Bag_01a",
        "name": "麻袋 (Bag)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Bag_01a",
        "bounding_box": {"x": 80, "y": 50, "z": 30},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Bag_01a_Stack": {
        "file_number": "SM_Bag_01a_Stack",
        "name": "麻袋堆叠 (Bag Stack)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Bag_01a_Stack",
        "bounding_box": {"x": 120, "y": 80, "z": 120},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Bag_02a": {
        "file_number": "SM_Bag_02a",
        "name": "编织袋 (Bag v2)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Bag_02a",
        "bounding_box": {"x": 80, "y": 50, "z": 25},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Bag_02a_Stack": {
        "file_number": "SM_Bag_02a_Stack",
        "name": "编织袋堆叠 (Bag v2 Stack)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Bag_02a_Stack",
        "bounding_box": {"x": 120, "y": 80, "z": 100},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Barrel_01a": {
        "file_number": "SM_Barrel_01a",
        "name": "铁桶 (Barrel)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Barrel_01a",
        "bounding_box": {"x": 60, "y": 60, "z": 90},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Beam_01_10m": {
        "file_number": "SM_Beam_01_10m",
        "name": "工字钢 10m (I-Beam)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Beam_01_10m",
        "bounding_box": {"x": 1000, "y": 20, "z": 20},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Beam_02_5m": {
        "file_number": "SM_Beam_02_5m",
        "name": "方钢 5m (Square Beam)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Beam_02_5m",
        "bounding_box": {"x": 500, "y": 15, "z": 15},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "download_url": ""
    },
    "SM_Beer_Keg_01a": {
        "file_number": "SM_Beer_Keg_01a",
        "name": "不锈钢桶 (Keg)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Beer_Keg_01a",
        "bounding_box": {"x": 40, "y": 40, "z": 50},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_01a": {
        "file_number": "SM_Box_01a",
        "name": "纸箱 (Box)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_01a",
        "bounding_box": {"x": 60, "y": 40, "z": 40},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Large_01a": {
        "file_number": "SM_Box_Large_01a",
        "name": "大纸箱 (Large Box)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Large_01a",
        "bounding_box": {"x": 120, "y": 80, "z": 80},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Long_01a": {
        "file_number": "SM_Box_Long_01a",
        "name": "长纸箱 (Long Box)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Long_01a",
        "bounding_box": {"x": 200, "y": 40, "z": 30},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Long_01a_Stack": {
        "file_number": "SM_Box_Long_01a_Stack",
        "name": "长纸箱堆叠 v1 (Long Box Stack)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Long_01a_Stack",
        "bounding_box": {"x": 200, "y": 40, "z": 120},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Long_02a": {
        "file_number": "SM_Box_Long_02a",
        "name": "长纸箱 v2 (Long Box v2)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Long_02a",
        "bounding_box": {"x": 200, "y": 40, "z": 30},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Long_02a_Stack": {
        "file_number": "SM_Box_Long_02a_Stack",
        "name": "长纸箱堆叠 v2 (Long Box v2 Stack)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Long_02a_Stack",
        "bounding_box": {"x": 200, "y": 40, "z": 120},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Small_01a": {
        "file_number": "SM_Box_Small_01a",
        "name": "小纸箱 (Small Box)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Small_01a",
        "bounding_box": {"x": 30, "y": 20, "z": 20},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Box_Small_01a_Stack": {
        "file_number": "SM_Box_Small_01a_Stack",
        "name": "小纸箱堆叠 (Small Box Stack)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Box_Small_01a_Stack",
        "bounding_box": {"x": 60, "y": 40, "z": 80},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Cable_Drum_01a": {
        "file_number": "SM_Cable_Drum_01a",
        "name": "线缆盘 v1 (Cable Drum)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Cable_Drum_01a",
        "bounding_box": {"x": 80, "y": 40, "z": 80},
        "supported_interfaces": ["I3D_Representable", "I3D_Spatial", "I3D_Visual"],
        "download_url": ""
    },
    "SM_Cable_Drum_01b": {
        "file_number": "SM_Cable_Drum_01b",
        "name": "线缆盘 v2 (Cable Drum)",
        "format": "uasset",
        "ue_path": "/Game/WarehouseProps_Bundle/Models/SM_Cable_Drum_01b",
        "bounding_box": {"x": 80, "y": 40, "z": 80},
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
