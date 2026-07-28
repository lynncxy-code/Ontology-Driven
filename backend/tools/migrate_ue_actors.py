"""
FR-6 历史 actor 一次性迁移（离线脚本，OntoTwin 3.4）
============================================================
把历史遗留、未经 ontotwin、未本体化的 UE actor "收编"成受管实例，灌进 PG。
这是**一次性离线工具**，不挂路由、豁免运行时"不新增"限制、人工把关、幂等可重跑。

数据契约
--------
输入（UE 编辑器脚本导出）：tools/ue_actors_export.json，见 *.sample.json：
    { project_id?, zone_id?, actors: [{ext_guid, name, mesh_asset, transform{tx..sz}}] }
assembly_v1 复合实例可额外携带 source_actor_guids、render_parts、
assembly_signature、unsupported_components。母 actor 仍只生成一个 OntoTwin 实例。
资产→类型映射：tools/mesh_type_mapping.json（见 *.sample.json）。匹配不上进 Legacy 桶。
输出：tools/ue_migration_result.json —— assembly_v1 结果文档，包含 instances 映射与
      delete_actor_guids；顶层同时保留旧版 {ext_guid: instance_id} 键，兼容旧 UE 读取器。

幂等
----
InstanceId 由 ext_guid 确定性派生（ue_<sanitized guid>）；且迁移前先读当前项目全部
实例（含上次迁移的），只增/更不误删——重复跑不产生重复实例。

⚠️ 需要可连的 PostgreSQL（ONTOTWIN_STORE 走 PG 后端）。UE 侧的导出/回写是另一块工作。

运行：
    docker compose run --rm backend python -m tools.migrate_ue_actors \
        [--input tools/ue_actors_export.json] [--mapping tools/mesh_type_mapping.json] [--dry-run]
"""

import os
import re
import json
import csv
import argparse
import uuid

from project_store import ProjectStore, _default_raw_state, apply_instance_metadata   # ONTOTWIN_STORE=pg 时自动是 PG 版
from db import pg
from ue_project_binding import bind_active_dataset

_HERE = os.path.dirname(__file__)
LEGACY_RID = "legacy.unclassified"
MIGRATION_RESULT_SCHEMA_VERSION = "assembly_v1"
LEGACY_TYPE = {
    "rid": LEGACY_RID,
    "name": "Legacy 未分类",
    "category": "Legacy",
    "description": "FR-6 迁移：未匹配到类型的历史 actor 兜底桶，待人工本体化。",
    "color": "#8a8a8a",
    "properties": [],
    "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
    "asset_id": None,
    "mock_instances": [],
    "source": "legacy",
}


def _sanitize_id(guid):
    return "ue_" + re.sub(r"[^0-9A-Za-z_-]", "", str(guid))


def _raw_from_transform(rid, name, mesh_asset, tf):
    raw = _default_raw_state(rid, name, {"x": tf.get("tx", 0), "y": tf.get("ty", 0), "z": tf.get("tz", 0)})
    raw["rotation_x"] = float(tf.get("rx", 0))
    raw["rotation_y"] = float(tf.get("ry", 0))
    raw["rotation_z"] = float(tf.get("rz", 0))
    raw["scale_x"] = float(tf.get("sx", 1))
    raw["scale_y"] = float(tf.get("sy", 1))
    raw["scale_z"] = float(tf.get("sz", 1))
    # 每 actor 自带资产：Legacy 类型无 type 级资产时，靠 raw.asset_id 让快照下发本 actor 的 mesh
    if mesh_asset:
        raw["asset_id"] = mesh_asset
    return raw


def _split_path(path):
    return [p.strip() for p in str(path or "").replace("\\", "/").split("/") if p.strip()]


def _best_asset_field(actor):
    for key in ("blueprint_class_path", "skeletal_mesh_asset", "static_mesh_asset", "mesh_asset", "actor_class_path"):
        value = actor.get(key)
        if value:
            return key, value
    return "", ""


def _first_render_asset(actor):
    """Return the first usable assembly part asset without changing the payload."""
    for part in actor.get("render_parts") or []:
        if not isinstance(part, dict):
            continue
        for key in ("asset_path", "ue_asset_path", "static_mesh_asset", "mesh_asset"):
            value = part.get(key)
            if value:
                return value
    return ""


def _best_asset_key(actor):
    return _best_asset_field(actor)[1] or _first_render_asset(actor)


def _classification_key(actor):
    signature = actor.get("assembly_signature")
    if signature:
        return f"assembly_signature:{signature}"
    field, asset = _best_asset_field(actor)
    if not asset:
        asset = _first_render_asset(actor)
        field = "render_part.asset_path" if asset else ""
    if asset:
        return f"{field}:{asset}"
    folder = actor.get("source_folder_path") or ""
    if folder:
        return f"folder:{folder}"
    return f"name:{actor.get('name') or actor.get('actor_label') or 'unknown'}"


def _source_actor_guids(actor):
    """Return the exact actor deletion set for one migrated mother actor."""
    values = [actor.get("ext_guid")]
    source_guids = actor.get("source_actor_guids") or []
    if not isinstance(source_guids, (list, tuple, set)):
        source_guids = [source_guids]
    values.extend(source_guids)

    result = []
    seen = set()
    for value in values:
        guid = str(value or "").strip()
        if guid and guid not in seen:
            seen.add(guid)
            result.append(guid)
    return result


def _render_config_from_actor(actor, injected_interfaces, fallback_asset):
    """Freeze instance-level rendering data, including an assembly_v1 payload."""
    config = {
        "injected_interfaces": list(injected_interfaces or []),
        "asset_id": fallback_asset or "",
        "ue_asset_path": fallback_asset or "",
    }
    for key in (
        "source_actor_guids",
        "render_parts",
        "assembly_signature",
        "unsupported_components",
    ):
        if key in actor:
            config[key] = actor[key]
    return config


def _build_migration_result(
    instances,
    delete_actor_guids,
    legacy_actor_mapping=None,
    blocked_actors=None,
):
    """Build the canonical result while retaining legacy top-level GUID lookups."""
    instance_mapping = dict(instances)
    document = {
        "schema_version": MIGRATION_RESULT_SCHEMA_VERSION,
        "instances": instance_mapping,
        "delete_actor_guids": list(delete_actor_guids),
        "blocked_actors": list(blocked_actors or []),
    }
    # Legacy UE code enumerates root GUID keys to delete migrated actors. UUID keys
    # cannot collide with the reserved schema keys, so aliases for mother and child
    # actors are safe and let old projects consume the upgraded result during rollout.
    document.update(dict(legacy_actor_mapping or instance_mapping))
    return document


def _unsupported_components(actor):
    """Normalize exporter findings that make automatic source cleanup unsafe."""
    findings = actor.get("unsupported_components") or []
    if not isinstance(findings, (list, tuple, set)):
        findings = [findings]
    return [finding for finding in findings if finding]


def _classification_action(rule):
    return ((rule or {}).get("action") or "").strip().lower()


def _load_classification_csv(path):
    if not path:
        return {}
    rules = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("group_key") or "").strip()
            if not key:
                continue
            rules[key] = row
    return rules


def _migration_rid(group_key):
    return f"ri.obj.{uuid.uuid5(uuid.NAMESPACE_URL, 'ontotwin:migration:' + group_key)}"


def _is_create_experimental(rule):
    return bool(rule) and (rule.get("action") or "").strip().lower() == "create_experimental"


def _experimental_type(rid, rule, source_asset):
    name = (rule.get("suggested_object_type_name") or "").strip() or rid
    return {
        "rid": rid,
        "name": name,
        "category": "UE Migration",
        "description": "Created from UE migration classification CSV; review before promoting.",
        "color": "#8a8a8a",
        "properties": [],
        "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
        "asset_id": None,
        "mock_instances": [],
        "source": "ue_migration",
        "lifecycle_status": "EXPERIMENTAL",
        "graph_rid": rid,
        "source_asset_path": source_asset,
        "classification_key": (rule.get("group_key") or "").strip(),
    }


def _ensure_dataset_type_node(active_proj, ot):
    if not active_proj or not active_proj.get("dataset"):
        return
    ds = active_proj["dataset"]
    graph_data = ds.setdefault("graph_data", {"nodes": [], "links": [], "categories": []})
    nodes = graph_data.setdefault("nodes", [])
    rid = ot.get("rid")
    if any(n.get("rid") == rid or n.get("id") == rid for n in nodes):
        return
    category = ot.get("category") or "UE Migration"
    nodes.append({
        "id": rid,
        "rid": rid,
        "name": ot.get("name") or rid,
        "category": category,
        "description": ot.get("description", ""),
        "injected_interfaces": ot.get("injected_interfaces", []),
        "color": ot.get("color", "#8a8a8a"),
        "properties": ot.get("properties", []),
    })
    cats = graph_data.setdefault("categories", [])
    if not any(c.get("name") == category for c in cats):
        cats.append({"name": category})
    ds["node_count"] = len(nodes)
    ds["link_count"] = len(graph_data.get("links") or [])


def _metadata_from_actor(actor, rule, rid, source_asset):
    label = actor.get("actor_label") or actor.get("name") or actor.get("ext_guid") or ""
    source_folder = actor.get("source_folder_path") or ""
    if rule and (rule.get("hierarchy_path") or "").strip():
        hierarchy_path = _split_path(rule.get("hierarchy_path"))
    elif source_folder:
        hierarchy_path = ["历史迁移"] + _split_path(source_folder)
    else:
        hierarchy_path = ["历史迁移", "未分类"]
    status = (rule or {}).get("classification_status") or ("confirmed" if rid != LEGACY_RID else "needs_review")
    return {
        "display_name": label,
        "hierarchy_path": hierarchy_path,
        "source_folder_path": source_folder,
        "source_asset_path": source_asset,
        "classification_status": status,
        "classification_key": _classification_key(actor),
    }


def migrate(
    input_path,
    mapping_path,
    classification_csv=None,
    dry_run=False,
    allow_unsupported=False,
):
    # 仅当运行时后端是 PG 时才要求 PG 可达（跟随 ONTOTWIN_STORE，与运行中后端一致，
    # 避免"迁移写 PG、运行时读 JSON"的双真源劈叉）
    if os.environ.get("ONTOTWIN_STORE", "json").lower() == "pg" and not pg.ping():
        raise SystemExit("PG 连不上：先起 db 服务并确认 DATABASE_URL")

    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    actors = payload.get("actors") or []
    target_pid = payload.get("project_id")
    zone_id = payload.get("zone_id")
    ue_project_id = (payload.get("ue_project_id") or "").strip()
    ue_project_name = (payload.get("ue_project_name") or "").strip()

    mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    classification_rules = _load_classification_csv(classification_csv)

    store = ProjectStore()
    if target_pid and target_pid != store.get_active_id():
        if not store.activate(target_pid):
            raise SystemExit(f"目标项目不存在或无法激活：{target_pid}")
    if store.get_active() is None:
        raise SystemExit("当前无激活项目，且输入未指定可用 project_id")

    active_proj = store.get_active() or {}
    active_ds = active_proj.get("dataset") or {}
    bound_ue_project_id = (active_ds.get("bound_ue_project_id") or "").strip()
    if ue_project_id:
        if bound_ue_project_id and bound_ue_project_id != ue_project_id:
            raise SystemExit(
                f"UE 工程不匹配：当前项目已绑定 {bound_ue_project_id}，"
                f"但导出 JSON 来自 {ue_project_id}"
            )
        if not dry_run:
            ok, info = bind_active_dataset(store, ue_project_id, ue_project_name)
            if not ok:
                raise SystemExit(f"绑定 UE 工程失败：{info}")
    elif bound_ue_project_id:
        raise SystemExit(
            f"导出 JSON 缺少 ue_project_id，但当前项目已绑定 {bound_ue_project_id}。"
            "请用新版 UE 插件重新导出。"
        )
    else:
        print("警告：导出 JSON 未提供 ue_project_id；按旧导出兼容模式迁移，不建立 UE 工程绑定。")

    print(f"存储后端={store.__class__.__name__} | 目标项目={store.get_active_id()}"
          f"（{(store.get_active() or {}).get('name')}）")

    ots = dict(store.get_object_types())
    insts = store.get_active().get("instances") or {}
    # ext_guid → 已有实例 id（幂等）
    by_guid = {v.get("ext_guid"): k for k, v in insts.items() if v.get("ext_guid")}

    instance_mapping = {}
    legacy_actor_mapping = {}
    delete_actor_guids = []
    delete_guid_seen = set()
    blocked_actors = []
    stats = {
        "new": 0,
        "updated": 0,
        "matched": 0,
        "legacy": 0,
        "skipped": 0,
        "blocked": 0,
    }
    need_legacy = False

    for a in actors:
        guid = a.get("ext_guid")
        if not guid:
            print(f"跳过（无 ext_guid）: {a.get('name')}")
            continue
        mesh = (
            a.get("mesh_asset")
            or a.get("static_mesh_asset")
            or a.get("skeletal_mesh_asset")
            or _first_render_asset(a)
            or ""
        )
        tf = a.get("transform") or {}

        group_key = _classification_key(a)
        rule = classification_rules.get(group_key)
        action = _classification_action(rule)
        if action in {"skip", "exclude", "ignore"}:
            stats["skipped"] += 1
            print(f"跳过（分类 action={action}）: {a.get('name') or guid}")
            continue

        unsupported = _unsupported_components(a)
        if unsupported and not allow_unsupported:
            stats["blocked"] += 1
            blocked_actors.append({
                "ext_guid": guid,
                "name": a.get("name") or a.get("actor_label") or guid,
                "unsupported_components": unsupported,
            })
            print(
                f"阻止迁移（含 {len(unsupported)} 个不支持项，不会加入清理名单）: "
                f"{a.get('name') or guid}"
            )
            continue
        source_asset = _best_asset_key(a) or mesh
        rid = (rule or {}).get("suggested_object_type_rid")
        if not rid and _is_create_experimental(rule):
            rid = _migration_rid(group_key)
        rid = rid or mapping.get(source_asset) or mapping.get(mesh)
        if rid and rid in ots:
            stats["matched"] += 1
        elif rid and _is_create_experimental(rule):
            ot = _experimental_type(rid, rule, source_asset)
            ots[rid] = ot
            _ensure_dataset_type_node(store.get_active(), ot)
            stats["matched"] += 1
        else:
            rid = LEGACY_RID
            need_legacy = True
            stats["legacy"] += 1

        iid = by_guid.get(guid) or _sanitize_id(guid)
        rec = {
            "id": iid,
            "object_type_rid": rid,
            "object_type_name": ots.get(rid, {}).get("name", rid),
            "zone_id": zone_id,
            "source": "ue_migrated",
            "ext_guid": guid,
            "render_config": _render_config_from_actor(
                a,
                ots.get(rid, LEGACY_TYPE).get("injected_interfaces", []),
                mesh,
            ),
            "raw_state": _raw_from_transform(rid, a.get("name"), mesh, tf),
        }
        apply_instance_metadata(rec, _metadata_from_actor(a, rule, rid, source_asset))
        if iid in insts:
            # 保留原 created_at
            rec["created_at"] = insts[iid].get("created_at")
            stats["updated"] += 1
        else:
            import time as _t
            rec["created_at"] = _t.time()
            stats["new"] += 1
        rec.setdefault("last_seen", rec["created_at"])
        rec["status"] = "online"
        insts[iid] = rec
        instance_mapping[guid] = iid
        for source_guid in _source_actor_guids(a):
            legacy_actor_mapping[source_guid] = iid
            if source_guid not in delete_guid_seen:
                delete_guid_seen.add(source_guid)
                delete_actor_guids.append(source_guid)

    if need_legacy and LEGACY_RID not in ots:
        ots[LEGACY_RID] = dict(LEGACY_TYPE)

    if need_legacy:
        active_proj = store.get_active()
        if active_proj and "dataset" in active_proj and active_proj["dataset"]:
            ds = active_proj["dataset"]
            if "graph_data" in ds:
                nodes = ds["graph_data"].setdefault("nodes", [])
                if not any(n.get("rid") == LEGACY_RID for n in nodes):
                    nodes.append({
                        "id": LEGACY_RID,
                        "rid": LEGACY_RID,
                        "name": LEGACY_TYPE["name"],
                        "category": LEGACY_TYPE["category"],
                        "description": LEGACY_TYPE["description"],
                        "injected_interfaces": LEGACY_TYPE["injected_interfaces"],
                        "color": LEGACY_TYPE["color"],
                        "properties": LEGACY_TYPE["properties"],
                    })
                    ds["node_count"] = len(nodes)
                    print(f"已将 {LEGACY_RID} 节点追加至项目数据集的图谱节点中")

    if not need_legacy and LEGACY_RID in ots and not any(
        inst.get("object_type_rid") == LEGACY_RID for inst in insts.values()
    ):
        ots.pop(LEGACY_RID, None)
        active_proj = store.get_active()
        if active_proj and active_proj.get("dataset"):
            graph_data = active_proj["dataset"].setdefault("graph_data", {"nodes": [], "links": [], "categories": []})
            graph_data["nodes"] = [
                n for n in graph_data.get("nodes", [])
                if n.get("rid") != LEGACY_RID and n.get("id") != LEGACY_RID
            ]
            active_proj["dataset"]["node_count"] = len(graph_data.get("nodes") or [])

    print("拟迁移统计:", stats, "| Legacy 桶:", "新建" if (need_legacy and LEGACY_RID not in store.get_object_types()) else "复用/无")

    result = _build_migration_result(
        instance_mapping,
        delete_actor_guids,
        legacy_actor_mapping,
        blocked_actors,
    )

    if dry_run:
        print("[dry-run] 未写库。迁移结果预览:", json.dumps(result, ensure_ascii=False))
        return result

    store.set_object_types(ots)         # 落 Legacy 类型（若有）
    store.get_active()["instances"] = insts
    store._save_current()

    out_path = os.path.join(_HERE, "ue_migration_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"完成：{stats} → 已写库。assembly_v1 迁移结果：{out_path}（供 UE 回写/清理原 Actor）")
    print("⚠ 运行中的后端把激活项目缓存在内存——请重启后端使迁移结果生效："
          "docker compose restart backend")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=os.path.join(_HERE, "ue_actors_export.json"))
    ap.add_argument("--mapping", default=os.path.join(_HERE, "mesh_type_mapping.json"))
    ap.add_argument("--classification-csv", default=None,
                    help="可选：由 generate_migration_classification_csv.py 生成并人工编辑后的分类表")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--allow-unsupported",
        action="store_true",
        help="显式允许迁移含不支持组件/负缩放的组合；默认阻止并排除出清理名单",
    )
    args = ap.parse_args()
    migrate(
        args.input,
        args.mapping,
        args.classification_csv,
        args.dry_run,
        args.allow_unsupported,
    )
