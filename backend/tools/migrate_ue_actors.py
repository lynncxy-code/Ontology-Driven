"""
FR-6 历史 actor 一次性迁移（离线脚本，OntoTwin 3.4）
============================================================
把历史遗留、未经 ontotwin、未本体化的 UE actor "收编"成受管实例，灌进 PG。
这是**一次性离线工具**，不挂路由、豁免运行时"不新增"限制、人工把关、幂等可重跑。

数据契约
--------
输入（UE 编辑器脚本导出）：tools/ue_actors_export.json，见 *.sample.json：
    { project_id?, zone_id?, actors: [{ext_guid, name, mesh_asset, transform{tx..sz}}] }
资产→类型映射：tools/mesh_type_mapping.json（见 *.sample.json）。匹配不上进 Legacy 桶。
输出：tools/ue_migration_result.json —— {ext_guid: instance_id}，供 UE 侧把 InstanceId
      写回对应 actor（收编完成，之后走正向流程被 ontotwin 修改）。

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
import argparse

from project_store import ProjectStore, _default_raw_state   # ONTOTWIN_STORE=pg 时自动是 PG 版
from db import pg

_HERE = os.path.dirname(__file__)
LEGACY_RID = "legacy.unclassified"
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


def migrate(input_path, mapping_path, dry_run=False):
    # 仅当运行时后端是 PG 时才要求 PG 可达（跟随 ONTOTWIN_STORE，与运行中后端一致，
    # 避免"迁移写 PG、运行时读 JSON"的双真源劈叉）
    if os.environ.get("ONTOTWIN_STORE", "json").lower() == "pg" and not pg.ping():
        raise SystemExit("PG 连不上：先起 db 服务并确认 DATABASE_URL")

    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    actors = payload.get("actors") or []
    target_pid = payload.get("project_id")
    zone_id = payload.get("zone_id")

    mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    store = ProjectStore()
    if target_pid and target_pid != store.get_active_id():
        if not store.activate(target_pid):
            raise SystemExit(f"目标项目不存在或无法激活：{target_pid}")
    if store.get_active() is None:
        raise SystemExit("当前无激活项目，且输入未指定可用 project_id")
    print(f"存储后端={store.__class__.__name__} | 目标项目={store.get_active_id()}"
          f"（{(store.get_active() or {}).get('name')}）")

    ots = dict(store.get_object_types())
    insts = store.get_active().get("instances") or {}
    # ext_guid → 已有实例 id（幂等）
    by_guid = {v.get("ext_guid"): k for k, v in insts.items() if v.get("ext_guid")}

    result = {}
    stats = {"new": 0, "updated": 0, "matched": 0, "legacy": 0}
    need_legacy = False

    for a in actors:
        guid = a.get("ext_guid")
        if not guid:
            print(f"跳过（无 ext_guid）: {a.get('name')}")
            continue
        mesh = a.get("mesh_asset") or ""
        tf = a.get("transform") or {}

        rid = mapping.get(mesh)
        if rid and rid in ots:
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
            "render_config": {
                "injected_interfaces": ots.get(rid, LEGACY_TYPE).get("injected_interfaces", []),
                "asset_id": mesh,
                "ue_asset_path": mesh,
            },
            "raw_state": _raw_from_transform(rid, a.get("name"), mesh, tf),
        }
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
        result[guid] = iid

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

    print("拟迁移统计:", stats, "| Legacy 桶:", "新建" if (need_legacy and LEGACY_RID not in store.get_object_types()) else "复用/无")

    if dry_run:
        print("[dry-run] 未写库。id 映射预览:", json.dumps(result, ensure_ascii=False))
        return result

    store.set_object_types(ots)         # 落 Legacy 类型（若有）
    store.get_active()["instances"] = insts
    store._save_current()

    out_path = os.path.join(_HERE, "ue_migration_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"完成：{stats} → 已写库。id 映射输出：{out_path}（供 UE 回写 InstanceId）")
    print("⚠ 运行中的后端把激活项目缓存在内存——请重启后端使迁移结果生效："
          "docker compose restart backend")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=os.path.join(_HERE, "ue_actors_export.json"))
    ap.add_argument("--mapping", default=os.path.join(_HERE, "mesh_type_mapping.json"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    migrate(args.input, args.mapping, args.dry_run)
