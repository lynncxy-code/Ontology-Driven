"""
ProjectStore (v2.9.4 数据模型重构)
============================================================
统一数据模型:一个 Project = 一个工厂/楼层场景的全部自洽数据。

    Project {
        id            稳定唯一 id（创建时生成，永不变）
        name          显示名（如 "我的工厂SCC 5F"）
        created_at
        object_types  该项目的类型注册表（原 _object_types 的内容）
        instances     该项目的实例 { instance_id: {...} }
        calibration   坐标标定（变换矩阵+锚点），可空
    }

存储:一项目一文件 data/projects/{id}.json + data/active.json（激活态）。
内存:只保留"当前激活项目"一份；非激活项目不进内存、不参与任何过滤。
取代原 InstanceStore + 散落的 _datasets / _active_dataset_id 全局。

唯一可见性规则:一切只认"当前激活项目"。
"""

import json
import os
import time
import threading

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PROJECTS_DIR = os.path.join(_DATA_DIR, "projects")
_ACTIVE_FILE = os.path.join(_DATA_DIR, "active.json")


def _safe_id(pid):
    """项目 id → 安全的 ASCII 文件名。"""
    s = str(pid)
    keep = "".join(c for c in s if c.isascii() and (c.isalnum() or c in ("-", "_")))
    return keep or "project"


def _default_raw_state(object_type_rid, object_type_name, initial_position):
    """实例初始 raw_state（沿用原 InstanceStore 的默认值约定）。"""
    pos = initial_position or {}
    raw = {
        "translation_x": float(pos.get("x", 0)),
        "translation_y": float(pos.get("y", 0)),
        "translation_z": float(pos.get("z", 0)),
        "rotation_x": 0.0, "rotation_y": 0.0, "rotation_z": 0.0,
        "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
        "material_variant": "normal",
        "animation_state": "idle",
        "fx_trigger": "",
        "ui_label_content": object_type_name or object_type_rid,
        "status": "normal",
    }
    if "airplane" in object_type_rid:
        raw.update({"altitude": 1000.0, "speed": 850.0, "heading": 0.0})
    elif "agv" in object_type_rid:
        raw.update({"battery_level": 85.0, "speed": 1.2})
    elif "tooling" in object_type_rid:
        raw.update({"temperature": 22.0, "pressure": 101.3})
    return raw


class ProjectStore:
    def __init__(self, projects_dir=None, active_file=None):
        self._lock = threading.RLock()
        self._projects_dir = projects_dir or _PROJECTS_DIR
        self._active_file = active_file or _ACTIVE_FILE
        os.makedirs(self._projects_dir, exist_ok=True)
        self._active_id = None
        self._current = None   # 当前激活项目的完整内存对象（dict）
        self._dirty = False    # 当前项目实例是否有未落盘的高频改动
        self._load_active()

    # ── 底层 IO ──────────────────────────────────────────────
    def _path(self, pid):
        return os.path.join(self._projects_dir, _safe_id(pid) + ".json")

    def _write_json(self, path, obj):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, path)   # 原子替换

    def _read_project(self, pid):
        path = self._path(pid)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_current(self):
        if self._current:
            self._write_json(self._path(self._current["id"]), self._current)
            self._dirty = False

    def _load_active(self):
        if os.path.exists(self._active_file):
            try:
                with open(self._active_file, "r", encoding="utf-8") as f:
                    self._active_id = json.load(f).get("active_project_id")
            except Exception:
                self._active_id = None
        if self._active_id:
            self._current = self._read_project(self._active_id)
            if self._current is None:
                self._active_id = None

    def _save_active(self):
        self._write_json(self._active_file, {"active_project_id": self._active_id})

    # ── 项目级 ───────────────────────────────────────────────
    def list_projects(self):
        out = []
        if not os.path.isdir(self._projects_dir):
            return out
        for fn in os.listdir(self._projects_dir):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self._projects_dir, fn), "r", encoding="utf-8") as f:
                    p = json.load(f)
                out.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "created_at": p.get("created_at"),
                    "type_count": len(p.get("object_types") or {}),
                    "instance_count": len(p.get("instances") or {}),
                    "active": p.get("id") == self._active_id,
                })
            except Exception:
                pass
        return out

    def create_project(self, name, object_types=None, calibration=None,
                       project_id=None, dataset=None):
        """新建项目并设为激活。project_id 不传则自动生成稳定 id。
        dataset = 原数据集字典(含 graph_data),供前端语义图谱用。"""
        with self._lock:
            pid = project_id or f"p_{int(time.time() * 1000)}"
            proj = {
                "id": pid,
                "name": name,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataset": dataset,
                "object_types": object_types or {},
                "instances": {},
                "calibration": calibration,
            }
            self._write_json(self._path(pid), proj)
            self._current = proj
            self._active_id = pid
            self._save_active()
            return proj

    def get_active_dataset(self):
        with self._lock:
            return self._current.get("dataset") if self._current else None

    def set_dataset(self, dataset):
        with self._lock:
            if self._current:
                self._current["dataset"] = dataset
                self._save_current()

    def all_datasets(self):
        """所有项目里存的数据集字典(用于重建 _datasets 全局)。"""
        out = []
        for fn in os.listdir(self._projects_dir):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self._projects_dir, fn), "r", encoding="utf-8") as f:
                    p = json.load(f)
                if p.get("dataset"):
                    out.append(p["dataset"])
            except Exception:
                pass
        return out

    def activate(self, pid):
        with self._lock:
            if self._dirty:
                self._save_current()
            proj = self._read_project(pid)
            if proj is None:
                return False
            self._current = proj
            self._active_id = pid
            self._save_active()
            return True

    def deactivate(self):
        """无激活项目（如切到内置 demo）→ 不服务任何实例。"""
        with self._lock:
            if self._dirty:
                self._save_current()
            self._current = None
            self._active_id = None
            self._save_active()

    def delete_project(self, pid):
        with self._lock:
            path = self._path(pid)
            existed = os.path.exists(path)
            if existed:
                os.remove(path)
            if self._active_id == pid:
                self._active_id = None
                self._current = None
                self._save_active()
            return existed

    def get_active(self):
        with self._lock:
            return self._current

    def get_active_id(self):
        with self._lock:
            return self._active_id

    # ── 类型注册表（当前项目） ──────────────────────────────
    def get_object_types(self):
        with self._lock:
            return self._current["object_types"] if self._current else {}

    def set_object_types(self, object_types):
        with self._lock:
            if self._current:
                self._current["object_types"] = object_types
                self._save_current()

    # ── 标定（当前项目） ────────────────────────────────────
    def get_calibration(self):
        with self._lock:
            return self._current.get("calibration") if self._current else None

    def set_calibration(self, calibration):
        with self._lock:
            if self._current:
                self._current["calibration"] = calibration
                self._save_current()

    # ── 实例（当前项目） ────────────────────────────────────
    def _inst(self):
        return self._current["instances"] if self._current else {}

    @property
    def _instances(self):
        """兼容旧 InstanceStore：暴露当前项目实例 dict（app.py 有直接访问处）。"""
        return self._current["instances"] if self._current else {}

    def spawn(self, instance_id, object_type_rid, initial_position=None, render_config=None):
        with self._lock:
            if not self._current:
                return None
            ot = (self._current["object_types"] or {}).get(object_type_rid, {})
            rec = {
                "id": instance_id,
                "object_type_rid": object_type_rid,
                "object_type_name": ot.get("name", object_type_rid),
                "render_config": render_config or {},
                "created_at": time.time(),
                "last_seen": time.time(),
                "status": "online",
                "raw_state": _default_raw_state(object_type_rid, ot.get("name"), initial_position),
            }
            self._current["instances"][instance_id] = rec
            self._save_current()
            return rec

    def remove(self, instance_id):
        with self._lock:
            inst = self._inst().pop(instance_id, None)
            if inst is not None:
                self._save_current()
            return inst

    def get_raw_state(self, instance_id):
        with self._lock:
            inst = self._inst().get(instance_id)
            return dict(inst["raw_state"]) if inst else None

    def get_render_config(self, instance_id):
        with self._lock:
            inst = self._inst().get(instance_id)
            return dict(inst.get("render_config") or {}) if inst else None

    def update_raw_state(self, instance_id, patch, persist=False):
        """persist=True 才落盘（模拟器高频波动传 False，避免狂写磁盘）。"""
        with self._lock:
            inst = self._inst().get(instance_id)
            if not inst:
                return False
            inst["raw_state"].update(patch)
            inst["last_seen"] = time.time()
            if persist:
                self._save_current()
            else:
                self._dirty = True
            return True

    def touch(self, instance_id):
        with self._lock:
            inst = self._inst().get(instance_id)
            if inst:
                inst["last_seen"] = time.time()

    def get_all_ids(self):
        with self._lock:
            return list(self._inst().keys())

    def list_all(self):
        """实例元信息列表（含在线状态），仅当前项目。"""
        with self._lock:
            now = time.time()
            result = []
            for iid, inst in self._inst().items():
                result.append({
                    "id": iid,
                    "object_type_rid": inst["object_type_rid"],
                    "object_type_name": inst["object_type_name"],
                    "status": "online" if (now - inst["last_seen"]) < 3.0 else "offline",
                    "last_seen": inst["last_seen"],
                    "created_at": inst["created_at"],
                })
            return result

    def clear_instances(self):
        """清空当前项目的全部实例（保留项目与类型表）。"""
        with self._lock:
            if self._current:
                self._current["instances"] = {}
                self._save_current()

    def flush(self):
        """把高频改动落盘（可由后台定时调用）。"""
        with self._lock:
            if self._dirty:
                self._save_current()
