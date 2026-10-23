"""
sync_types_from_graph.py —— 本体图库 → 项目类型表 单向同步（3.4 #2）
============================================================
把 Neo4j 本体图库确立为**语义唯一真源**后，项目类型表（ProjectStore /
ProjectStorePG 的 object_types）退化为「类型绑定缓存」：

    语义字段（name / description / injected_interfaces / lifecycle）
        ← 由图库单向刷新（本工具做的事）
    绑定字段（asset_id / ue_asset_path / color / properties / mock_instances）
        ← 仍归项目类型表所有，本工具**绝不触碰**

匹配键：图库 ObjectType 的 x_block_name ↔ 项目类型表的 rid（如 "PE16A-3052"）。
方向：只读图、只写 store；**永不写图**（图的写入唯一走 build_ontology_json → 工具链灌库）。

用法（backend 容器内或 backend 目录）：
    python -m tools.sync_types_from_graph            # 默认 dry-run：只报告差异
    python -m tools.sync_types_from_graph --apply    # 把语义字段刷进类型表
    python -m tools.sync_types_from_graph --apply --add-missing
        # 额外把"图里有、表里没有"的类型补进表（新类型从上游/图库下发的通道）
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import graph                       # noqa: E402
from project_store import ProjectStore     # noqa: E402  ONTOTWIN_STORE=pg 时自动是 PG 版
from mapping_store import INTERFACES       # noqa: E402

project_store = ProjectStore()

# 图库接口 api_name（i3d_spatial）→ 运行时接口名（I3D_Spatial）
_IFACE_BY_API = {}
for _spec in INTERFACES:
    _api = _spec["rid"].lower()
    _IFACE_BY_API[_api] = _spec["rid"]


def sync(apply=False, add_missing=False):
    if not graph.ping():
        raise SystemExit("本体图库(Neo4j)不可达：先 docker compose up -d neo4j")
    if project_store.get_active() is None:
        raise SystemExit("当前无激活项目")

    reg = graph.fetch_registry()
    store_types = dict(project_store.get_object_types())

    graph_by_block = {}
    for o in reg["object_types"]:
        key = o.get("x_block_name") or o["api_name"]
        graph_by_block[key] = o

    updated, added, store_only = [], [], []

    # ── 语义字段：图 → 表 ────────────────────────────────────────────
    for rid, ot in store_types.items():
        g = graph_by_block.get(rid)
        if g is None:
            store_only.append(rid)
            continue
        injected = sorted(_IFACE_BY_API[a] for a in g["implements"] if a in _IFACE_BY_API)
        patch = {
            "name": g["display_name"],
            "injected_interfaces": injected,
            "lifecycle_status": g["lifecycle_status"],
            "graph_rid": g["rid"],           # 反向指针：表 → 图（后续按 UUID 对齐用）
        }
        changed = [k for k, v in patch.items() if ot.get(k) != v]
        if changed:
            updated.append((rid, changed))
            if apply:
                ot.update(patch)

    # ── 图里有、表里没有的类型 ──────────────────────────────────────
    for key, g in graph_by_block.items():
        if key in store_types:
            continue
        added.append(key)
        if apply and add_missing:
            injected = sorted(_IFACE_BY_API[a] for a in g["implements"] if a in _IFACE_BY_API)
            store_types[key] = {
                "rid": key,
                "name": g["display_name"],
                "category": "图库下发",
                "description": f"由本体图库同步新增（{g.get('x_source') or 'graph'}）",
                "color": "#8a8a8a",
                "properties": [],
                "injected_interfaces": injected,
                "asset_id": None,            # 绑定字段留空，待人工绑资产
                "mock_instances": [],
                "source": "graph_sync",
                "lifecycle_status": g["lifecycle_status"],
                "graph_rid": g["rid"],
            }

    if apply:
        project_store.set_object_types(store_types)

    # ── 报告 ────────────────────────────────────────────────────────
    mode = "已落库" if apply else "dry-run（加 --apply 落库）"
    print(f"[{mode}] 语义刷新 {len(updated)} | 图库新增 {len(added)}"
          f"{'（已补入）' if (apply and add_missing) else '（默认只报告，--add-missing 才补入）' if added else ''}"
          f" | 仅表里有 {len(store_only)}")
    for rid, changed in updated[:10]:
        print(f"  ~ {rid}: {', '.join(changed)}")
    if len(updated) > 10:
        print(f"  ... 等共 {len(updated)} 个")
    for k in added[:10]:
        print(f"  + 图库有/表缺: {k}")
    for k in store_only[:10]:
        print(f"  ! 表有/图缺: {k}（请重跑 build_ontology_json 并灌库）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="把语义字段写进类型表（默认 dry-run）")
    ap.add_argument("--add-missing", action="store_true", help="连同图里有表里没有的类型一起补入")
    args = ap.parse_args()
    sync(apply=args.apply, add_missing=args.add_missing)
