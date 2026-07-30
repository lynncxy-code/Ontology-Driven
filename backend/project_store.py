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
import copy

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PROJECTS_DIR = os.path.join(_DATA_DIR, "projects")
_ACTIVE_FILE = os.path.join(_DATA_DIR, "active.json")

CURRENT_SCHEMA_VERSION = 5


def _default_media_policy():
    """Project media policy inherits the deployment allowlist until explicitly restricted."""
    return {
        "revision": 0,
        "mode": "inherit_platform",
        "allowed_hosts": [],
        "http_exceptions": [],
    }


def _as_graph_dataset(project_id, project_name, project_created_at, dataset):
    """Return a detached graph dataset catalog entry, or None for project-only metadata."""
    if not isinstance(dataset, dict) or not isinstance(dataset.get("graph_data"), dict):
        return None

    normalized = copy.deepcopy(dataset)
    normalized["id"] = normalized.get("id") or project_id
    if not normalized["id"]:
        return None
    normalized["name"] = normalized.get("name") or project_name or normalized["id"]
    normalized["created_at"] = (
        normalized.get("created_at")
        or (str(project_created_at) if project_created_at is not None else "")
    )

    graph = normalized["graph_data"]
    nodes = graph.get("nodes")
    links = graph.get("links")
    if normalized.get("node_count") is None:
        normalized["node_count"] = len(nodes) if isinstance(nodes, list) else 0
    if normalized.get("link_count") is None:
        normalized["link_count"] = len(links) if isinstance(links, list) else 0
    return normalized


class UnsupportedProjectSchemaError(RuntimeError):
    pass


def migrate_project_schema(proj):
    """Upgrade an in-memory project to the current schema. Returns True when changed."""
    if not isinstance(proj, dict):
        raise ValueError("project must be an object")

    raw_version = proj.get("schema_version", 1)
    if isinstance(raw_version, bool):
        raise ValueError("schema_version must be an integer")
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise ValueError("schema_version must be an integer") from exc

    if version > CURRENT_SCHEMA_VERSION:
        raise UnsupportedProjectSchemaError(
            f"project schema v{version} is newer than supported v{CURRENT_SCHEMA_VERSION}"
        )
    if version < 1:
        raise ValueError(f"unsupported project schema version: {version}")

    changed = False
    if version == 1:
        # v2 formally versions the project and adds optional interface config containers.
        # Existing types and instances remain untouched until a capability is configured.
        proj["schema_version"] = 2
        version = 2
        changed = True

    if version == 2:
        # v3 introduces project-level scene interaction configuration. Migration never
        # enables roaming or invents project asset ids.
        proj.setdefault("scene_interactions", _default_scene_interactions())
        proj["schema_version"] = 3
        version = 3
        changed = True

    if version == 3:
        # v4 persists project-scoped image frames and authored roaming routes.
        # Migration only adds disabled/empty containers. It never invents an image,
        # UE ground reference or route point for an existing project.
        scene = proj.get("scene_interactions")
        if not isinstance(scene, dict):
            scene = _default_scene_interactions()
            proj["scene_interactions"] = scene
        scene.setdefault("routes", [])
        profile = proj.get("spatial_profile")
        if not isinstance(profile, dict):
            profile = _default_spatial_profile()
            proj["spatial_profile"] = profile
        floors = profile.get("floor_table")
        if not isinstance(floors, list) or not floors:
            floors = _default_spatial_profile()["floor_table"]
            profile["floor_table"] = floors
        for floor in floors:
            if not isinstance(floor, dict):
                continue
            floor_number = floor.get("floor", 1)
            floor.setdefault("floor_id", f"floor-{floor_number}")
            floor.setdefault("ue_ground_z_cm", None)
        proj.setdefault("frames", [])
        proj["schema_version"] = 4
        version = 4
        changed = True

    if version == 4:
        # v5 adds project-scoped media restrictions. Existing projects inherit the
        # deployment policy and remain unable to play media until an Overlay video
        # template is explicitly configured.
        proj.setdefault("media_policy", _default_media_policy())
        proj["schema_version"] = 5
        version = 5
        changed = True

    if proj.get("schema_version") != CURRENT_SCHEMA_VERSION:
        proj["schema_version"] = CURRENT_SCHEMA_VERSION
        changed = True
    return changed


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


def _clean_hierarchy_path(value, fallback):
    """Normalize instance hierarchy path to a non-empty list of display segments."""
    if isinstance(value, str):
        parts = value.replace("\\", "/").split("/")
    elif isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = fallback
    cleaned = []
    for part in parts or []:
        text = str(part or "").strip()
        if text:
            cleaned.append(text)
    return cleaned or [str(fallback[0] if fallback else "未分类")]


def apply_instance_metadata(rec, metadata=None):
    """Attach display/tree metadata shared by OntoTwin UI and UE Outliner folders."""
    metadata = metadata or {}
    type_name = rec.get("object_type_name") or rec.get("object_type_rid") or "未分类"
    rec["display_name"] = (metadata.get("display_name") or rec.get("display_name") or rec.get("id") or "").strip()
    rec["hierarchy_path"] = _clean_hierarchy_path(
        metadata.get("hierarchy_path", rec.get("hierarchy_path")),
        [type_name],
    )
    rec["source_folder_path"] = (metadata.get("source_folder_path") or rec.get("source_folder_path") or "").strip()
    rec["source_asset_path"] = (metadata.get("source_asset_path") or rec.get("source_asset_path") or "").strip()
    rec["classification_status"] = (
        metadata.get("classification_status") or rec.get("classification_status") or "confirmed"
    ).strip()
    rec["classification_key"] = (metadata.get("classification_key") or rec.get("classification_key") or "").strip()
    return rec


def _default_spatial_profile():
    """3.1 空间剖面默认值。规范系=mm；规范→UE 默认恒等（matrix=None 表示未标定，
    回退到 calibration 旧矩阵），保证旧项目/未标定项目行为不变。"""
    return {
        "unit": "mm",
        "canonical_origin": [0.0, 0.0],
        "ue_transform": {
            "display": {"axis_map": {"x": "+x", "y": "+y"}, "flip": False, "rotation_deg": 0},
            "matrix": None,              # 规范→UE 精确仿射（锚点拟合）；None=未标定
            "ue_origin_cm": [0.0, 0.0],
            "scale_to_cm": 0.1,
        },
        "floor_table": [
            {
                "floor": 1,
                "floor_id": "floor-1",
                "z_base_mm": 0.0,
                "ue_ground_z_cm": None,
                "ue_level": "",
                "map_codes": [],
            }
        ],
    }


def _default_scene_interactions():
    """Project-level scene interaction container; disabled after migration."""
    return {
        "revision": 0,
        "roaming": {
            "enabled": False,
            "auto_enter": False,
        },
        "routes": [],
    }


class ProjectMismatch(Exception):
    def __init__(self, expected, actual):
        super().__init__(f"active project changed: expected={expected} actual={actual}")
        self.expected = expected
        self.actual = actual


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

    @staticmethod
    def _ensure_collections(proj):
        """向后兼容：旧项目无 components/instance_roster 时补空，不影响现有数据。"""
        if proj is not None:
            proj.setdefault("components", {})
            proj.setdefault("instance_roster", [])
            proj.setdefault("scene_interactions", _default_scene_interactions())
            proj.setdefault("media_policy", _default_media_policy())
        return proj

    def _read_project(self, pid):
        path = self._path(pid)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                proj = json.load(f)
            migrate_project_schema(proj)
            proj = self._ensure_collections(proj)
            return proj
        except UnsupportedProjectSchemaError:
            raise
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
                ds = p.get("dataset") or {}
                insts = p.get("instances") or {}
                zones = {r.get("zone_id") for r in insts.values() if isinstance(r, dict) and r.get("zone_id")}
                unzoned = sum(1 for r in insts.values() if isinstance(r, dict) and not r.get("zone_id"))
                out.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "created_at": p.get("created_at"),
                    "schema_version": p.get("schema_version", 1),
                    "type_count": len(p.get("object_types") or {}),
                    "instance_count": len(insts),
                    "zone_count": len(zones),
                    "unzoned_instance_count": unzoned,
                    "bound_ue_project_id": ds.get("bound_ue_project_id", ""),
                    "bound_ue_project_name": ds.get("bound_ue_project_name", ""),
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
                "schema_version": CURRENT_SCHEMA_VERSION,
                "id": pid,
                "name": name,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataset": dataset,
                "object_types": object_types or {},
                "instances": {},
                "components": {},          # 3.0：坐标标定产出的匿名构件
                "instance_roster": [],     # 3.0：业务实例清单（身份证号目录）
                "calibration": calibration,
                "spatial_profile": _default_spatial_profile(),  # 3.1：空间剖面
                "frames": [],              # 3.1：通用帧注册表（CAD 帧标定后写入）
                "scene_interactions": _default_scene_interactions(),  # 4.0：场景交互能力
                "media_policy": _default_media_policy(),  # 3.7.x：视频来源安全策略
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
                dataset = _as_graph_dataset(
                    p.get("id"), p.get("name"), p.get("created_at"), p.get("dataset")
                )
                if dataset:
                    out.append(dataset)
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

    def get_active_copy(self):
        """Return a detached project snapshot for feature services and API responses."""
        with self._lock:
            return copy.deepcopy(self._current) if self._current else None

    def transact_active(self, updater):
        """Apply one low-frequency project update atomically and persist it once."""
        with self._lock:
            if not self._current:
                raise RuntimeError("no active project")
            previous = self._current
            working = copy.deepcopy(previous)
            result = updater(working)
            self._current = working
            try:
                self._save_current()
            except Exception:
                self._current = previous
                raise
            return result

    def transact_expected_active(self, expected_id, updater):
        """Atomic write with optional active-project guard, all under one lock."""
        with self._lock:
            if not self._current:
                raise RuntimeError("no active project")
            if expected_id is not None and self._active_id != expected_id:
                raise ProjectMismatch(expected_id, self._active_id)
            previous = self._current
            working = copy.deepcopy(previous)
            result = updater(working)
            self._current = working
            try:
                self._save_current()
            except Exception:
                self._current = previous
                raise
            return result

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

    # ── 场景交互（4.0：项目级低频配置） ────────────────────────
    def get_scene_interactions(self):
        with self._lock:
            if not self._current:
                return _default_scene_interactions()
            value = self._current.get("scene_interactions")
            if not isinstance(value, dict):
                value = _default_scene_interactions()
                self._current["scene_interactions"] = value
                self._save_current()
            return copy.deepcopy(value)

    def set_scene_interactions(self, scene_interactions):
        with self._lock:
            if self._current:
                self._current["scene_interactions"] = copy.deepcopy(
                    scene_interactions or _default_scene_interactions()
                )
                self._save_current()

    # ── 媒体策略（3.7.x：项目级低频安全配置） ───────────────────
    def get_media_policy(self):
        with self._lock:
            if not self._current:
                return _default_media_policy()
            value = self._current.get("media_policy")
            if not isinstance(value, dict):
                value = _default_media_policy()
                self._current["media_policy"] = value
                self._save_current()
            return copy.deepcopy(value)

    def set_media_policy(self, media_policy):
        with self._lock:
            if self._current:
                self._current["media_policy"] = copy.deepcopy(
                    media_policy or _default_media_policy()
                )
                self._save_current()

    # ── 实例（当前项目） ────────────────────────────────────
    def _inst(self):
        return self._current["instances"] if self._current else {}

    @property
    def _instances(self):
        """兼容旧 InstanceStore：暴露当前项目实例 dict（app.py 有直接访问处）。"""
        return self._current["instances"] if self._current else {}

    def spawn(self, instance_id, object_type_rid, initial_position=None, render_config=None, metadata=None,
              expected_project_id=None):
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
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
            apply_instance_metadata(rec, metadata)
            self._current["instances"][instance_id] = rec
            self._save_current()
            return rec

    def remove(self, instance_id, expected_project_id=None):
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
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

    def update_raw_state(self, instance_id, patch, persist=False, expected_project_id=None):
        """persist=True 才落盘（模拟器高频波动传 False，避免狂写磁盘）。"""
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
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

    def get_all_ids(self, zone_id=None):
        """当前项目实例 id 列表；zone_id 非空则只返回该分区（FR-3 分区过滤）。"""
        with self._lock:
            insts = self._inst()
            if zone_id is None:
                return list(insts.keys())
            return [iid for iid, r in insts.items() if r.get("zone_id") == zone_id]

    def assign_zone(self, instance_ids, zone_id):
        """批量设置实例分区；zone_id=None 表示解除分区，一次持久化全部变更。"""
        with self._lock:
            if not self._current:
                return {
                    "project_id": None,
                    "zone_id": zone_id,
                    "updated": [],
                    "unchanged": [],
                    "missing": list(instance_ids or []),
                }

            updated = []
            unchanged = []
            missing = []
            instances = self._inst()
            for instance_id in instance_ids or []:
                instance = instances.get(instance_id)
                if instance is None:
                    missing.append(instance_id)
                    continue
                current_zone = instance.get("zone_id") or None
                if current_zone == zone_id:
                    unchanged.append(instance_id)
                    continue
                if zone_id is None:
                    instance.pop("zone_id", None)
                else:
                    instance["zone_id"] = zone_id
                updated.append(instance_id)

            if updated:
                self._save_current()
            return {
                "project_id": self._active_id,
                "zone_id": zone_id,
                "updated": updated,
                "unchanged": unchanged,
                "missing": missing,
            }

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
                    "zone_id": inst.get("zone_id") or None,
                    "display_name": inst.get("display_name") or iid,
                    "hierarchy_path": _clean_hierarchy_path(
                        inst.get("hierarchy_path"),
                        [inst.get("object_type_name") or inst.get("object_type_rid") or "未分类"],
                    ),
                    "source_folder_path": inst.get("source_folder_path", ""),
                    "source_asset_path": inst.get("source_asset_path", ""),
                    "classification_status": inst.get("classification_status", "confirmed"),
                    "classification_key": inst.get("classification_key", ""),
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

    # ── 构件（3.0：坐标标定产物） ──────────────────────────────
    def _comps(self):
        return self._current["components"] if self._current else {}

    def get_components(self):
        with self._lock:
            return self._comps()

    def set_components(self, components):
        """整体替换当前项目的构件集（坐标标定"保存构件"调用）。"""
        with self._lock:
            if self._current:
                self._current["components"] = components or {}
                self._save_current()

    def clear_components(self):
        with self._lock:
            if self._current:
                self._current["components"] = {}
                self._save_current()

    def save_component_bundle(self, expected_project_id, profile_patch,
                              frame_patch, component_plan, mode="publish"):
        """坐标标定"保存构件"的组合事务：一次持锁内依次应用
        spatial_profile / frame / components，末尾只 `_save_current()` 一次。

        合并规则与三个独立 setter **逐字一致**，只是搬到工作副本上：
          - profile（对齐 set_spatial_profile）：整体替换。profile_patch 为待写入的
            完整 spatial_profile；None 表示本次不动 profile（例如图片源）。
          - frame（对齐 upsert_frame）：按 id upsert——命中即整条替换、否则追加。
            frame_patch 为 None 表示不动 frames。
          - components（对齐 set_components）：component_plan={"mode","components"}。
            mode=="publish" → 整体替换（清空后写入）；其余 → 并入现有集合。

        expected_project_id 非 None 时在锁内校验激活项目，不符抛 ProjectMismatch。
        """
        component_plan = component_plan or {}
        plan_mode = component_plan.get("mode") or mode
        new_comps = component_plan.get("components") or {}

        def _apply(w):
            if profile_patch is not None:
                w["spatial_profile"] = profile_patch or _default_spatial_profile()
            if frame_patch:
                frames = w.setdefault("frames", [])
                fid = frame_patch.get("id")
                for i, f in enumerate(frames):
                    if f.get("id") == fid:
                        frames[i] = frame_patch
                        break
                else:
                    frames.append(frame_patch)
            comps = w.setdefault("components", {})
            if plan_mode == "publish":
                comps.clear()
            comps.update(new_comps)
            return {"ok": True, "saved": len(comps), "component_count": len(comps)}

        return self.transact_expected_active(expected_project_id, _apply)

    def get_component_by_instance(self, instance_id):
        """按已绑定身份证号反查构件（FR-7 单实例微调用）。"""
        with self._lock:
            for c in self._comps().values():
                if c.get("bound_instance_id") == instance_id:
                    return c
            return None

    def update_component(self, component_id, patch, expected_project_id=None):
        """局部更新单个构件字段（如 canonical_xy / ue_xy / rotation），落盘。"""
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            comp = self._comps().get(component_id)
            if not comp:
                return False
            comp.update(patch or {})
            self._save_current()
            return True

    # ── 空间剖面 / 帧（3.1） ──────────────────────────────────
    def get_spatial_profile(self):
        with self._lock:
            if not self._current:
                return _default_spatial_profile()
            sp = self._current.get("spatial_profile")
            if not sp:                       # 旧项目无此字段 → 注入默认
                sp = _default_spatial_profile()
                self._current["spatial_profile"] = sp
                self._save_current()
            return sp

    def set_spatial_profile(self, profile, expected_project_id=None):
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            if self._current:
                self._current["spatial_profile"] = profile or _default_spatial_profile()
                self._save_current()

    def list_frames(self):
        with self._lock:
            return list(self._current.get("frames") or []) if self._current else []

    def get_frame(self, frame_id):
        with self._lock:
            for f in (self._current.get("frames") or []) if self._current else []:
                if f.get("id") == frame_id:
                    return f
            return None

    def upsert_frame(self, frame, expected_project_id=None):
        """按 id 新增/更新一帧。"""
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            if not self._current:
                return
            self._current.setdefault("frames", [])
            frames = self._current["frames"]
            fid = frame.get("id")
            for i, f in enumerate(frames):
                if f.get("id") == fid:
                    frames[i] = frame
                    break
            else:
                frames.append(frame)
            self._save_current()

    # ── 实例清单（3.0：身份证号目录） ─────────────────────────
    def get_roster(self):
        with self._lock:
            return list(self._current["instance_roster"]) if self._current else []

    def set_roster(self, roster):
        with self._lock:
            if self._current:
                self._current["instance_roster"] = roster or []
                self._save_current()

    def add_roster_entries(self, entries, expected_project_id=None):
        """追加清单行，按 instance_id 去重（已存在则覆盖）。

        expected_project_id 非 None 时在锁内、写之前校验激活项目，不符抛
        ProjectMismatch（消除 handler 级 check-then-act 的 TOCTOU）；缺省 None
        跳过校验，旧行为不变。
        """
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            if not self._current:
                return
            roster = self._current["instance_roster"]
            by_id = {e.get("instance_id"): e for e in roster if e.get("instance_id")}
            for e in entries or []:
                iid = e.get("instance_id")
                if iid:
                    by_id[iid] = e
            self._current["instance_roster"] = list(by_id.values())
            self._save_current()

    # ── 绑定（构件 ↔ 身份证号，1:1） ──────────────────────────
    def _bind_into(self, working, component_id, instance_id):
        """在工作副本上做「构件存在 + 目标身份证号 1:1 未占用」校验并写入。

        不落盘、不加锁——由调用方（bind / bind_batch）在锁内决定何时保存。
        成功时改写 working["components"][component_id]["bound_instance_id"]，返回 (True, None)；
        失败时不改动 working，返回 (False, reason)。
        """
        comps = (working.get("components") if working else None) or {}
        comp = comps.get(component_id)
        if not comp:
            return False, "构件不存在"
        # 1:1：该身份证号不能已被别的构件占用
        for cid, c in comps.items():
            if cid != component_id and c.get("bound_instance_id") == instance_id:
                return False, f"身份证号 {instance_id} 已绑定其他构件"
        comp["bound_instance_id"] = instance_id
        return True, None

    def bind(self, component_id, instance_id, expected_project_id=None):
        """把构件绑到身份证号；1:1 占用校验。返回 (ok, err)。"""
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            ok, reason = self._bind_into(self._current, component_id, instance_id)
            if ok:
                self._save_current()
            return ok, reason

    def bind_batch(self, pairs, expected_project_id=None):
        """单锁批事务：逐对在工作副本上校验+写，末尾只保存一次；无成功项则不保存。

        返回 {"bound": n, "failed": [{"component_id", "instance_id", "reason"}]}。
        绝不跨项目、绝不每条各自落盘。
        """
        with self._lock:
            if not self._current:
                raise RuntimeError("no active project")
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            working = copy.deepcopy(self._current)
            bound, failed = 0, []
            for p in pairs or []:
                cid = p.get("component_id")
                iid = (p.get("instance_id") or "").strip()
                ok, reason = self._bind_into(working, cid, iid)
                if ok:
                    bound += 1
                else:
                    failed.append({"component_id": cid, "instance_id": iid, "reason": reason})
            if bound:
                self._current = working
                self._save_current()
            return {"bound": bound, "failed": failed}

    def unbind(self, component_id, expected_project_id=None):
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            comp = self._comps().get(component_id)
            if not comp:
                return False
            comp["bound_instance_id"] = None
            self._save_current()
            return True

    # ── 铸造（已绑定构件 → 实例） ──────────────────────────────
    # will_update 只比这些"业务字段"，排除 last_seen/created_at 等时间字段，
    # 否则每次铸造都会因 last_seen 刷新而全量误报 update。
    _MINT_BUSINESS_FIELDS = ("object_type_rid", "object_type_name", "component_id", "render_config")

    def _plan_mint(self, snapshot, now):
        """纯规划函数：只读 snapshot、不改 snapshot、不落库、不取时钟。

        逐条深拷贝旧实例后再改，构造与 snapshot 完全分离的 result_instances。
        `now`（时间戳）由调用方传入，planner 内不再调 time.time()，保证同一次
        铸造里所有新增/刷新的时间戳一致且可预测。

        语义与原 mint_instances 完全一致（3.4.3）：不与"已绑定构件集"强对齐——
        result 先携带旧实例全集（保留 UE 历史/其他来源自由实例），再对已绑定
        构件 upsert；已存在实例保留其 raw_state 且不重置在线状态。
        """
        comps = snapshot.get("components", {}) or {}
        old = snapshot.get("instances", {}) or {}
        # 3.1：楼层 → Z 基准(cm) 查表（沿用原实现）
        sp = snapshot.get("spatial_profile") or _default_spatial_profile()
        scale = (sp.get("ue_transform") or {}).get("scale_to_cm", 0.1)
        floor_z_cm = {}
        for ft in sp.get("floor_table") or []:
            floor_z_cm[ft.get("floor")] = float(ft.get("z_base_mm", 0)) * scale

        # 先深拷贝旧实例全集（原实现的 new_instances = dict(old)：保留自由实例），
        # 深拷贝确保对入参零改动。
        result = copy.deepcopy(old)
        to_create, to_update = [], []
        for comp in comps.values():
            iid = comp.get("bound_instance_id")
            if not iid:
                continue
            ot_rid = comp.get("object_type_rid", "")
            if iid in old:
                rec = copy.deepcopy(old[iid])          # 逐条深拷贝，勿改入参
                new_render = comp.get("render_config") or rec.get("render_config") or {}
                new_name = comp.get("type_name", ot_rid)
                # will_update 判定唯一遍历 _MINT_BUSINESS_FIELDS，消除魔法字面量、
                # 避免与常量双真源漂移；仍排除 last_seen/created_at（不在该元组内）。
                new_vals = {
                    "object_type_rid": ot_rid,
                    "object_type_name": new_name,
                    "component_id": comp.get("id"),
                    "render_config": new_render,
                }
                changed = any(rec.get(f) != new_vals[f] for f in self._MINT_BUSINESS_FIELDS)
                rec["component_id"] = comp.get("id")
                rec["object_type_rid"] = ot_rid
                rec["object_type_name"] = new_name
                rec["render_config"] = new_render
                rec["last_seen"] = now
                if changed:
                    to_update.append(iid)
            else:
                pos = {"x": (comp.get("ue_xy") or [0, 0])[0],
                       "y": (comp.get("ue_xy") or [0, 0])[1],
                       "z": floor_z_cm.get(comp.get("floor", 1), 0.0)}
                rec = {
                    "id": iid,
                    "component_id": comp.get("id"),
                    "object_type_rid": ot_rid,
                    "object_type_name": comp.get("type_name", ot_rid),
                    "render_config": comp.get("render_config") or {},
                    "created_at": now,
                    "last_seen": now,
                    "status": "online",
                    "raw_state": _default_raw_state(ot_rid, comp.get("type_name"), pos),
                }
                to_create.append(iid)
            apply_instance_metadata(rec)
            result[iid] = rec
        return {"to_create": to_create, "to_update": to_update, "result_instances": result}

    def mint_instances(self, dry_run=False, expected_project_id=None):
        """把所有已绑定构件同步为实例；dry_run 与真写共用同一段规划逻辑。

        返回 dict：{"minted": n, "to_create": [...], "to_update": [...]}。
        （历史签名返回 int 计数，本任务起改为 dict——调用方 app.py 由 Task 6 适配。）
        dry_run=True 只出规划、minted=0、不落库；dry_run=False 落库并计已绑定构件数。
        expected_project_id 非空且与当前激活项目不符时抛 ProjectMismatch（全程持锁）。
        """
        now = time.time()
        with self._lock:
            if not self._current:
                return {"minted": 0, "to_create": [], "to_update": []}
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            snapshot = copy.deepcopy(self._current)
            plan = self._plan_mint(snapshot, now)
            if dry_run:
                return {"minted": 0, "to_create": plan["to_create"], "to_update": plan["to_update"]}
            self._current["instances"] = plan["result_instances"]
            self._save_current()
            # minted 沿用原语义：已绑定构件数（非 result 全集，后者含保留的自由实例）。
            minted = len([c for c in (snapshot.get("components") or {}).values()
                          if c.get("bound_instance_id")])
            return {"minted": minted, "to_create": plan["to_create"], "to_update": plan["to_update"]}


# ── 存储后端开关（3.4）─────────────────────────────────────────
# 默认 JSON（行为零变化）；ONTOTWIN_STORE=pg 时切到 PostgreSQL 后端。
# 通过重绑本模块的 ProjectStore 名，app.py 的 `from project_store import ProjectStore`
# 自动拿到对应实现，无需改 app.py。
import os as _os
if _os.environ.get("ONTOTWIN_STORE", "json").lower() == "pg":
    try:
        from project_store_pg import ProjectStorePG as ProjectStore  # noqa: F811
    except Exception as _e:
        import sys as _sys
        print(f"[project_store] PG 后端加载失败，回退 JSON 版: {_e}", file=_sys.stderr)
