import os
import time
import math
import requests as http_requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from ontology import SharedState
from mapping_store import (
    MappingStore, ONTOLOGY_PROPERTIES, INTERFACES, INTERFACE_MAP,
    TRANSFORM_TYPES, MOCK_ASSETS, OBJECT_TYPES,
    InstanceStore, MockInstanceSimulator
)
from ontology_parser import validate_files, parse_ontology_csvs

# ── App Setup ───────────────────────────────────────────────────
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
app.json.ensure_ascii = False  # 中文字符不转义为 \uXXXX，便于 2.9.2 调试（Flask 2.2+ 用法）
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

@app.route('/cad_generator')
def serve_cad_generator():
    return app.send_static_file('cad_generator.html')

@app.route('/coord')
def serve_coord_workbench():
    return app.send_static_file('coord_workbench.html')

@app.route('/floor_pulse')
def serve_floor_pulse():
    return app.send_static_file('floor_pulse.html')

@app.route('/scenes')
def serve_scenes():
    return app.send_static_file('scenes/scenes.html')


# ═══════════════════════════════════════════════════════════════
# PRD 2.9 — 坐标标定工作台 API（无状态）
# ═══════════════════════════════════════════════════════════════

import json as _json
import tempfile
from parser_dxf import extract_preview_data
from coord_transform import calibrate as coord_calibrate, apply_transform as coord_apply

_MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'block_asset_mapping.json')

@app.route('/api/v2/coord/preview', methods=['POST'])
def coord_preview():
    """DXF 上传解析，返回预览数据（仅 CAD 模式）"""
    if 'file' not in request.files:
        return jsonify({"error": "未检测到上传文件"}), 400
    
    f = request.files['file']
    if not f.filename.lower().endswith('.dxf'):
        return jsonify({"error": "仅支持 .dxf 文件"}), 400
    
    # 写入临时文件供 ezdxf 读取
    tmp = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
    try:
        f.save(tmp.name)
        tmp.close()
        result = extract_preview_data(tmp.name)
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass


@app.route('/api/v2/coord/types/scan', methods=['POST'])
def coord_types_scan():
    """
    PRD 2.9.2 § 4.4 — 扫描 DXF，返回候选 ObjectType 列表。
    上传 file=<dxf>，返回 { summary, candidates, filtered_log, dxf_encoding }
    """
    if 'file' not in request.files:
        return jsonify({"error": "未检测到上传文件"}), 400

    f = request.files['file']
    if not f.filename.lower().endswith('.dxf'):
        return jsonify({"error": "仅支持 .dxf 文件"}), 400

    # 读 block_asset_mapping.json 用于 preset_asset_id 预填
    mapping = {}
    if os.path.exists(_MAPPING_FILE):
        try:
            with open(_MAPPING_FILE, 'r', encoding='utf-8') as mf:
                mapping = _json.load(mf) or {}
        except Exception:
            mapping = {}

    tmp = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
    try:
        f.save(tmp.name)
        tmp.close()
        from parser_dxf import extract_block_candidates
        result = extract_block_candidates(tmp.name, mapping=mapping)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"DXF 解析失败: {str(e)}"}), 500
    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass


def _item_to_node(item, source_file=None):
    """
    把 commit 请求中的一个 item 转为数据集 node 格式（与 _project_dataset_to_object_types 的输入一致）。
    PRD 2.9.2 § 9 — 平铺结构 + source 字段。
    """
    block_name = item.get("block_name") or item.get("rid")
    name = (item.get("name") or block_name or "").strip()
    return {
        "rid": block_name,                      # rid 强制 = block_name
        "name": name or block_name,
        "category": item.get("category") or "Core",
        "description": item.get("description") or (
            f"由 CAD 解析自动创建（来源：{source_file}）" if source_file else ""
        ),
        "color": item.get("color") or "#0891b2",
        "properties": item.get("properties") or [],
        "injected_interfaces": item.get("injected_interfaces") or [
            "I3D_Representable", "I3D_Spatial"
        ],
        "asset_id": (item.get("asset_id") or "").strip() or None,
        "mock_instances": [],
        "source": f"cad_auto:{source_file}" if source_file else item.get("source"),
        "created_at": time.time(),
    }


def _write_back_asset_mapping(items):
    """把 items 中非空 asset_id 回写至 block_asset_mapping.json。返回写入条数。"""
    existing = {}
    if os.path.exists(_MAPPING_FILE):
        try:
            with open(_MAPPING_FILE, 'r', encoding='utf-8') as f:
                existing = _json.load(f) or {}
        except Exception:
            existing = {}
    n = 0
    for it in items:
        bn = it.get("block_name") or it.get("rid")
        ai = (it.get("asset_id") or "").strip()
        if bn and ai:
            existing[bn] = ai
            n += 1
    if n > 0:
        try:
            with open(_MAPPING_FILE, 'w', encoding='utf-8') as f:
                _json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"WARN: asset mapping 回写失败: {e}")
    return n


@app.route('/api/v2/coord/types/commit', methods=['POST'])
def coord_types_commit():
    """
    PRD 2.9.2 § 10 — 提交审核结果，发布新数据集或合并到现有数据集。

    Body: {
        "source_file": "新块.dxf",
        "mode": "publish" | "merge",
        "items": [...],
        "publish_options": { "name": "..." },
        "merge_options":   { "target_dataset_id": "..." },
        "conflict_strategy": "skip" | "overwrite",   // merge 模式
        "force": bool                                // 跳过副作用警告
    }
    """
    global _datasets, _active_dataset_id, _object_types

    import datetime
    data = request.json or {}
    mode = data.get("mode", "publish")
    items = data.get("items") or []
    source_file = data.get("source_file") or ""
    force = bool(data.get("force"))

    if not items:
        return jsonify({"error": "items 为空，请至少勾选一项"}), 400

    if mode == "publish":
        return _commit_publish(data, items, source_file, force)
    elif mode == "merge":
        return _commit_merge(data, items, source_file, force)
    else:
        return jsonify({"error": f"未知 mode: {mode}"}), 400


def _commit_publish(data, items, source_file, force):
    """publish 模式：新建数据集 + 默认激活 + 副作用检测。"""
    global _datasets, _active_dataset_id, _object_types
    import datetime

    opts = data.get("publish_options") or {}
    name = (opts.get("name") or "").strip()
    if not name:
        name = f"cad:{source_file or 'untitled'}"

    # 重名检测（漏洞 11）
    existing = [ds for ds in _datasets if ds["name"] == name]
    if existing:
        return jsonify({
            "error": "name_duplicated",
            "message": f"已存在同名数据集: {name}",
            "existing": [{"id": ds["id"], "name": ds["name"]} for ds in existing]
        }), 409

    # 构建 nodes
    nodes = [_item_to_node(it, source_file) for it in items]

    # 副作用预检：若激活新集，当前 _object_types 中"将被全量替换"的 rid 集合
    new_rid_set = {n["rid"] for n in nodes}
    old_rid_set = set(_object_types.keys())
    will_be_lost = old_rid_set - new_rid_set     # 被移除的
    will_be_overwritten = old_rid_set & new_rid_set  # 被覆盖的（但定义可能改了）
    affected_rids = list(will_be_lost) + list(will_be_overwritten)
    dangling = _detect_dangling_refs(affected_rids)
    if dangling and not force:
        return jsonify({
            "status": "pending_warnings",
            "mode": "publish",
            "dataset_name_to_create": name,
            "warnings": {
                "dangling_refs": dangling,
                "summary": f"切换激活数据集会让 {sum(d['instance_count'] for d in dangling)} 个实例的类型引用悬空"
            },
            "hint": "确认后请用 force=true 重新提交"
        })

    # 真正写入
    ds_id = f"ds_{int(datetime.datetime.now().timestamp() * 1000)}"
    while any(d["id"] == ds_id for d in _datasets):
        ds_id = ds_id + "_x"
    new_ds = {
        "id": ds_id,
        "name": name,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "node_count": len(nodes),
        "link_count": 0,
        "graph_data": {"nodes": nodes, "links": [], "categories": []}
    }
    _datasets.append(new_ds)
    _active_dataset_id = ds_id
    _object_types = _project_dataset_to_object_types(new_ds)
    mapping_n = _write_back_asset_mapping(items)

    return jsonify({
        "status": "ok",
        "mode": "publish",
        "dataset_id": ds_id,
        "dataset_name": name,
        "written_count": len(nodes),
        "asset_mapping_updated": mapping_n,
        "active_dataset_id": _active_dataset_id,
        "hint": "若其他标签页正在浏览语义图谱总览，请手动刷新查看新数据集"
    })


def _commit_merge(data, items, source_file, force):
    """merge 模式：追加/覆盖到目标数据集 + 同名冲突处理 + 副作用预检（仅当 target == active）。"""
    global _datasets, _active_dataset_id, _object_types

    opts = data.get("merge_options") or {}
    target_id = opts.get("target_dataset_id")
    strategy = data.get("conflict_strategy", "skip")  # skip | overwrite
    if not target_id:
        return jsonify({"error": "merge 模式必须提供 target_dataset_id"}), 400
    if target_id == "demo":
        return jsonify({"error": "Demo 数据集只读，不能合并"}), 400
    target_ds = next((d for d in _datasets if d["id"] == target_id), None)
    if not target_ds:
        return jsonify({"error": f"找不到数据集: {target_id}"}), 404
    if strategy not in ("skip", "overwrite"):
        return jsonify({"error": f"未知 conflict_strategy: {strategy}"}), 400

    # 构建新 nodes
    new_nodes = [_item_to_node(it, source_file) for it in items]
    new_rid_set = {n["rid"] for n in new_nodes}

    # 找出目标集中已存在的同 rid（冲突）
    target_nodes = (target_ds.get("graph_data") or {}).get("nodes", [])
    existing_rids = {n.get("rid") for n in target_nodes if n.get("rid")}
    collide = new_rid_set & existing_rids

    # 副作用预检：仅当 target == active（合并会刷新 _object_types）
    if target_id == _active_dataset_id and collide:
        # 被覆盖的 rid 中，被实例引用且 strategy=overwrite 的需要警告
        if strategy == "overwrite":
            dangling = _detect_dangling_refs(list(collide))
            if dangling and not force:
                return jsonify({
                    "status": "pending_warnings",
                    "mode": "merge",
                    "target_dataset_id": target_id,
                    "warnings": {
                        "dangling_refs": dangling,
                        "summary": f"覆盖会影响 {sum(d['instance_count'] for d in dangling)} 个实例引用的类型定义"
                    },
                    "hint": "确认后请用 force=true 重新提交，或改用 conflict_strategy=skip"
                })

    # 真正合并
    skipped = 0
    overwritten = 0
    added = 0
    final_nodes = list(target_nodes)  # 复制
    by_rid = {n.get("rid"): i for i, n in enumerate(final_nodes) if n.get("rid")}
    for nn in new_nodes:
        rid = nn["rid"]
        if rid in by_rid:
            if strategy == "skip":
                skipped += 1
            else:  # overwrite
                final_nodes[by_rid[rid]] = nn
                overwritten += 1
        else:
            final_nodes.append(nn)
            by_rid[rid] = len(final_nodes) - 1
            added += 1

    target_ds["graph_data"]["nodes"] = final_nodes
    target_ds["node_count"] = len(final_nodes)

    # 若目标是当前激活的，刷新 _object_types
    if target_id == _active_dataset_id:
        _object_types = _project_dataset_to_object_types(target_ds)

    mapping_n = _write_back_asset_mapping(items)

    return jsonify({
        "status": "ok",
        "mode": "merge",
        "target_dataset_id": target_id,
        "target_dataset_name": target_ds["name"],
        "added": added,
        "overwritten": overwritten,
        "skipped": skipped,
        "asset_mapping_updated": mapping_n,
        "active_dataset_id": _active_dataset_id,
        "hint": "若其他标签页正在浏览语义图谱总览，请手动刷新查看更新"
    })


@app.route('/api/v2/coord/types/check_conflicts', methods=['POST'])
def coord_types_check_conflicts():
    """
    PRD 2.9.2 § 8.4 — 给定将要写入的 rid 列表与目标数据集，返回冲突信息。

    Body: {
        "rids": ["SDT-0200-甲-3", "AGV", ...],     # 待写入的 rid 列表
        "mode": "publish" | "merge",
        "target_dataset_id": str   # 仅 merge 模式必填
    }
    Response: {
        "in_target_dataset": [{"rid": ..., "old": {...}}],   # 仅 merge 有意义
        "in_other_datasets": [{"rid": ..., "datasets": [{"id","name"}, ...]}]
    }
    """
    data = request.json or {}
    rids = data.get("rids") or []
    mode = data.get("mode", "publish")
    target_ds_id = data.get("target_dataset_id")

    rid_set = set(rids)
    in_target = []
    in_other = {}  # rid -> [(ds_id, ds_name)]

    for ds in _datasets:
        graph = ds.get("graph_data") or {}
        nodes = graph.get("nodes", []) if graph else []
        # Demo 数据集走 OBJECT_TYPES（其 graph_data=None）
        if ds["id"] == "demo":
            for rid, ot in OBJECT_TYPES.items():
                if rid in rid_set:
                    in_other.setdefault(rid, []).append({"id": ds["id"], "name": ds["name"]})
            continue
        for node in nodes:
            rid = node.get("rid")
            if rid in rid_set:
                if mode == "merge" and ds["id"] == target_ds_id:
                    in_target.append({"rid": rid, "old": node})
                else:
                    in_other.setdefault(rid, []).append({"id": ds["id"], "name": ds["name"]})

    return jsonify({
        "in_target_dataset": in_target,
        "in_other_datasets": [
            {"rid": rid, "datasets": dss} for rid, dss in in_other.items()
        ]
    })


@app.route('/api/v2/coord/types/check_coverage', methods=['POST'])
def coord_types_check_coverage():
    """
    PRD 2.9.2 § 8.3.1 — "跳过此步"按钮的覆盖率检查。
    给定 block_name 列表，返回激活数据集中覆盖了哪些 / 缺失哪些。

    Body: { "block_names": ["SDT-0200-甲-3", ...] }
    Response: { total, covered, missing, missing_samples }
    """
    data = request.json or {}
    names = data.get("block_names") or []
    covered = [n for n in names if n in _object_types]
    missing = [n for n in names if n not in _object_types]
    return jsonify({
        "total": len(names),
        "covered": len(covered),
        "missing": len(missing),
        "missing_samples": missing[:10],
        "active_dataset_id": _active_dataset_id,
    })


def _derive_instance_id(item, rid):
    """instance_id 推导：优先 attribs.EQUIP_ID；缺失则 <rid>-<6位hash>。"""
    iid = (item.get("instance_id") or "").strip()
    if iid:
        return iid
    attribs = item.get("attribs") or {}
    eq = (attribs.get("EQUIP_ID") or attribs.get("equip_id") or "").strip()
    if eq:
        return eq
    # hash 兜底
    import hashlib
    seed = f"{rid}|{item.get('cad_xy')}|{item.get('rotation')}"
    h = hashlib.md5(seed.encode('utf-8')).hexdigest()[:6]
    return f"{rid}-{h}"


def _find_rid_in_other_datasets(rid):
    """返回该 rid 所在的（非激活）数据集列表，用于三态校验。"""
    hits = []
    for ds in _datasets:
        if ds["id"] == _active_dataset_id:
            continue
        graph = ds.get("graph_data") or {}
        # Demo 走 OBJECT_TYPES 常量
        if ds["id"] == "demo":
            if rid in OBJECT_TYPES:
                hits.append({"id": ds["id"], "name": ds["name"]})
            continue
        nodes = graph.get("nodes", []) if graph else []
        if any(n.get("rid") == rid for n in nodes):
            hits.append({"id": ds["id"], "name": ds["name"]})
    return hits


def _has_real_coord(raw_state):
    """坐标是否已设置（任一非 0 视为已部署）"""
    if not raw_state:
        return False
    for k in ("translation_x", "translation_y", "translation_z"):
        if abs(float(raw_state.get(k) or 0)) > 1e-6:
            return True
    return False


@app.route('/api/v2/coord/spawn_instances', methods=['POST'])
def coord_spawn_instances():
    """
    PRD 2.9.1 — 批量把 CAD/图片实体投入 InstanceStore。

    Body: {
        "source_label": "新块.dxf" | "image:xxx.png",
        "mode": "dxf" | "image",
        "transform_matrix": [[a,b,tx],[c,d,ty]],
        "items": [
            {"block_name": str, "cad_xy": [x,y], "rotation": float,
             "attribs": {"EQUIP_ID": ...}, "instance_id": str (可选, 覆盖推导)}
        ],
        "conflict_strategy": "update_coord" | "skip" | "duplicate",  # 默认 update_coord
        "commit": bool   # false=dry-run，true=真写入
    }
    """
    data = request.json or {}
    items = data.get("items") or []
    matrix = data.get("transform_matrix")
    commit = bool(data.get("commit"))
    mode = data.get("mode", "dxf")
    source_label = data.get("source_label") or ""
    strategy = data.get("conflict_strategy") or "update_coord"

    if not items:
        return jsonify({"error": "items 为空"}), 400
    if not matrix:
        return jsonify({"error": "缺少 transform_matrix（请先完成标定）"}), 400
    if strategy not in ("update_coord", "skip", "duplicate"):
        return jsonify({"error": f"未知 conflict_strategy: {strategy}"}), 400

    to_create = []
    to_update_coord_only = []
    conflicts = []
    errors = []
    warnings = []

    # 用于本批次内重名检测
    batch_iids = set()
    # 用于 duplicate 模式时的后缀计数
    suffix_counter = {}

    for item in items:
        block_name = (item.get("block_name") or "").strip()
        if not block_name:
            errors.append({"item": item, "reason": "block_name 为空"})
            continue

        # 1) 三态校验
        if block_name not in _object_types:
            other_dss = _find_rid_in_other_datasets(block_name)
            if other_dss:
                errors.append({
                    "block_name": block_name,
                    "reason": "type_not_in_active_dataset",
                    "found_in_datasets": other_dss,
                    "hint": f"该类型存在于数据集 '{other_dss[0]['name']}'，请先激活该数据集"
                })
            else:
                errors.append({
                    "block_name": block_name,
                    "reason": "type_not_found",
                    "found_in_datasets": [],
                    "hint": "请先在 2.9.2 中创建该类型"
                })
            continue

        # 2) 应用变换矩阵
        cad_xy = item.get("cad_xy")
        if not cad_xy or len(cad_xy) < 2:
            errors.append({"block_name": block_name, "reason": "cad_xy 缺失或非法"})
            continue
        try:
            ue_xy = coord_apply(matrix, cad_xy)
        except Exception as e:
            errors.append({"block_name": block_name, "reason": f"变换失败: {e}"})
            continue

        # 3) 推导 instance_id
        iid = _derive_instance_id(item, block_name)

        # 4) 批内重名（自动 -2/-3 后缀）
        original_iid = iid
        if iid in batch_iids:
            n = suffix_counter.get(original_iid, 1) + 1
            while f"{original_iid}-{n}" in batch_iids:
                n += 1
            iid = f"{original_iid}-{n}"
            suffix_counter[original_iid] = n
            warnings.append({
                "block_name": block_name, "original_id": original_iid, "renamed_to": iid,
                "reason": "批内重名已自动重命名"
            })
        batch_iids.add(iid)

        rotation = float(item.get("rotation") or 0.0)
        record = {
            "instance_id": iid,
            "object_type_rid": block_name,
            "translation_x": float(ue_xy[0]),
            "translation_y": float(ue_xy[1]),
            "translation_z": 0.0,
            "rotation_z": rotation,
            "cad_xy": cad_xy,
        }

        # ObjectType.asset_id 缺失警告
        ot = _object_types.get(block_name) or {}
        if not ot.get("asset_id"):
            warnings.append({
                "block_name": block_name, "instance_id": iid,
                "reason": "asset_id 缺失，UE 不会渲染该实例"
            })

        # 5) 与 InstanceStore 现有实例的冲突分类
        existing = instance_store._instances.get(iid)
        if existing is None:
            to_create.append(record)
        else:
            existing_rid = existing.get("object_type_rid")
            if existing_rid != block_name:
                errors.append({
                    "block_name": block_name, "instance_id": iid,
                    "reason": f"instance_id 已被类型 '{existing_rid}' 占用"
                })
                continue
            # 同类型，看坐标是否已设置
            if not _has_real_coord(existing.get("raw_state")):
                # 视为 2.3.1 / MES 注册但未部署 → 补充坐标（非冲突）
                to_update_coord_only.append(record)
            else:
                conflicts.append({**record, "existing": {
                    "translation_x": existing["raw_state"].get("translation_x"),
                    "translation_y": existing["raw_state"].get("translation_y"),
                }})

    # dry-run：返回预览不写
    summary = {
        "total": len(items),
        "to_create": len(to_create),
        "to_update_coord_only": len(to_update_coord_only),
        "conflicts": len(conflicts),
        "errors": len(errors),
        "warnings": len(warnings),
    }
    if not commit:
        return jsonify({
            "status": "dry_run",
            "summary": summary,
            "to_create": to_create,
            "to_update_coord_only": to_update_coord_only,
            "conflicts": conflicts,
            "errors": errors,
            "warnings": warnings,
        })

    # 真写入
    written_create = 0
    written_update = 0
    written_conflict = 0
    skipped_conflict = 0
    dup_records = []

    def _coord_patch(rec):
        return {
            "translation_x": rec["translation_x"],
            "translation_y": rec["translation_y"],
            "translation_z": rec["translation_z"],
            "rotation_z": rec["rotation_z"],
        }

    # 5.1 to_create — 全部 spawn
    for rec in to_create:
        instance_store.spawn(rec["instance_id"], rec["object_type_rid"], {
            "x": rec["translation_x"], "y": rec["translation_y"], "z": rec["translation_z"]
        })
        instance_store.update_raw_state(rec["instance_id"], {"rotation_z": rec["rotation_z"]})
        written_create += 1

    # 5.2 to_update_coord_only — 补充坐标
    for rec in to_update_coord_only:
        instance_store.update_raw_state(rec["instance_id"], _coord_patch(rec))
        written_update += 1

    # 5.3 conflicts — 按策略处理
    for rec in conflicts:
        if strategy == "update_coord":
            instance_store.update_raw_state(rec["instance_id"], _coord_patch(rec))
            written_conflict += 1
        elif strategy == "skip":
            skipped_conflict += 1
        elif strategy == "duplicate":
            new_iid = rec["instance_id"]
            n = 2
            while new_iid in instance_store._instances:
                new_iid = f"{rec['instance_id']}-{n}"; n += 1
            instance_store.spawn(new_iid, rec["object_type_rid"], {
                "x": rec["translation_x"], "y": rec["translation_y"], "z": rec["translation_z"]
            })
            instance_store.update_raw_state(new_iid, {"rotation_z": rec["rotation_z"]})
            dup_records.append({"original_id": rec["instance_id"], "new_id": new_iid})

    return jsonify({
        "status": "ok",
        "summary": {
            **summary,
            "written_create": written_create,
            "written_update": written_update,
            "written_conflict": written_conflict,
            "skipped_conflict": skipped_conflict,
            "duplicated": len(dup_records),
        },
        "duplicated": dup_records,
        "source_label": source_label,
        "mode": mode,
        "hint": "实例已写入 InstanceStore，可在 /instance 页面查看；UE 端将于下次轮询同步显示"
    })


@app.route('/api/v2/coord/calibrate', methods=['POST'])
def coord_calibrate_api():
    """锚点标定，返回仿射变换矩阵与精度指标"""
    data = request.json
    if not data or 'anchors' not in data:
        return jsonify({"success": False, "error": "missing_anchors", "message": "请提供锚点数据"}), 400
    
    anchors = data['anchors']
    if len(anchors) < 2:
        return jsonify({"success": False, "error": "insufficient_anchors", "message": "至少需要 2 组锚点"}), 400
    
    try:
        result = coord_calibrate(anchors)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"success": False, "error": "calibration_failed", "message": str(e)}), 400


@app.route('/api/v2/coord/export', methods=['POST'])
def coord_export():
    """导出场景 JSON（CAD 模式），坐标经仿射变换"""
    data = request.json
    if not data:
        return jsonify({"error": "请求体为空"}), 400
    
    matrix = data.get('transform_matrix')
    entities_in = data.get('entities', [])
    polylines_in = data.get('polylines', [])
    wall_height = data.get('wall_height', 4500)
    wall_thickness = data.get('wall_thickness', 240)
    
    if not matrix:
        return jsonify({"error": "缺少 transform_matrix"}), 400
    
    out_entities = []
    
    # 处理 INSERT 实体
    for ent in entities_in:
        if not ent.get('export', True):
            continue
        pos = ent.get('position', [0, 0])
        ue = coord_apply(matrix, pos)
        out_entities.append({
            "id": ent.get('id', ''),
            "layer": ent.get('layer', ''),
            "generate_type": "INSTANCE",
            "data": {
                "mesh_id": ent.get('asset_path', ent.get('block_name', '')),
                "transform": {
                    "loc": [ue[0], ue[1], 0],
                    "rot": [0, 0, ent.get('rotation', 0)],
                    "scale": [1, 1, 1]
                },
                "metadata": ent.get('attribs', {})
            }
        })
    
    # 处理 Polyline 实体
    for p in polylines_in:
        if not p.get('export', True):
            continue
        ue_pts = [coord_apply(matrix, pt) for pt in p.get('points', [])]
        gt = p.get('generate_type', 'PROCEDURAL_WALL')
        entry = {
            "id": p.get('id', ''),
            "layer": p.get('layer', ''),
            "generate_type": gt,
            "data": {"path": ue_pts}
        }
        if gt == 'PROCEDURAL_WALL':
            entry["data"]["height"] = wall_height
            entry["data"]["thickness"] = wall_thickness
        out_entities.append(entry)
    
    output = {
        "header": {
            "version": "1.0",
            "calibration": {
                "matrix": matrix,
                "anchor_count": data.get('anchor_count', 0)
            }
        },
        "entities": out_entities
    }
    
    return jsonify(output)


@app.route('/api/v2/coord/mapping', methods=['GET'])
def coord_mapping_get():
    """读取块名→资产路径全局映射"""
    try:
        with open(_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        mapping = {}
    return jsonify(mapping)


@app.route('/api/v2/coord/mapping', methods=['POST'])
def coord_mapping_save():
    """保存/合并块名→资产路径映射"""
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "请提供 JSON 对象"}), 400
    
    # 读取现有映射
    try:
        with open(_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        mapping = {}
    
    # 合并新数据
    mapping.update(data)
    
    with open(_MAPPING_FILE, 'w', encoding='utf-8') as f:
        _json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    return jsonify({"saved": True, "total_entries": len(mapping)})


# ═══════════════════════════════════════════════════════════════
# 数字脉搏 — OntoTwin Middleware 代理接口
# 默认对接 localhost:5001（可通过环境变量 ONTOTWIN_MIDDLEWARE_URL 覆盖）
# 运行中转站时请指定不同端口：ONTOTWIN_PORT=5001 python app.py
# ═══════════════════════════════════════════════════════════════

MIDDLEWARE_BASE_URL = os.environ.get('ONTOTWIN_MIDDLEWARE_URL', 'http://127.0.0.1:5001')

# ── Mock Override State ──
_fp_mock_enabled = False
_fp_mock_snapshot = {} # instanceId -> item dict
_fp_mock_events = []
_fp_mock_event_id = 9000000

@app.route('/api/v2/floor_pulse/mock/toggle', methods=['POST'])
def toggle_fp_mock():
    global _fp_mock_enabled, _fp_mock_snapshot, _fp_mock_events, _fp_mock_event_id
    data = request.json or {}
    _fp_mock_enabled = data.get("enabled", False)
    if not _fp_mock_enabled:
        _fp_mock_snapshot.clear()
        _fp_mock_events.clear()
    return jsonify({"enabled": _fp_mock_enabled})

@app.route('/api/v2/floor_pulse/mock/move', methods=['POST'])
def fp_mock_move():
    global _fp_mock_event_id
    if not _fp_mock_enabled:
        return jsonify({"error": "模拟开关未打开"}), 400
    
    data = request.json or {}
    instance_id = data.get("instanceId")
    ws_id = data.get("workstationId")
    ws_name = data.get("workstationName")
    if not instance_id or not ws_id:
        return jsonify({"error": "Missing params"}), 400

    import datetime
    now_iso = datetime.datetime.utcnow().isoformat() + 'Z'
    _fp_mock_event_id += 1

    # 休息区 WS-00 → idle，其他工位 → working
    status = "idle" if ws_id == "WS-00" else "working"

    # 构造事件
    event = {
        "messageType": "event",
        "eventId": _fp_mock_event_id,
        "eventType": "state_changed",
        "instanceId": instance_id,
        "entityType": "human",
        "version": 999,
        "occurredAt": now_iso,
        "from": None,
        "to": {
            "workstationId": ws_id,
            "workstationName": ws_name,
            "status": status
        }
    }
    _fp_mock_events.append(event)
    
    # 更新快照缓存
    if instance_id not in _fp_mock_snapshot:
        _fp_mock_snapshot[instance_id] = {}
    _fp_mock_snapshot[instance_id]["workstationId"] = ws_id
    _fp_mock_snapshot[instance_id]["workstationName"] = ws_name
    _fp_mock_snapshot[instance_id]["status"] = status

    return jsonify({"status": "ok", "eventId": _fp_mock_event_id})

@app.route('/api/v2/floor_pulse/snapshot')
def proxy_floor_pulse_snapshot():
    """代理拉取中转站快照，注入服务端时间戳"""
    import datetime
    try:
        resp = http_requests.get(f'{MIDDLEWARE_BASE_URL}/api/ue/snapshot', timeout=5)
        data = resp.json()
        
        # 注入 Mock 覆写
        if _fp_mock_enabled:
            for item in data.get("items", []):
                iid = item.get("instanceId")
                if iid in _fp_mock_snapshot:
                    if "state" not in item: item["state"] = {}
                    item["state"]["workstationId"] = _fp_mock_snapshot[iid]["workstationId"]
                    item["state"]["workstationName"] = _fp_mock_snapshot[iid]["workstationName"]
            if _fp_mock_events:
                data["latestEventId"] = _fp_mock_event_id

        data['_proxy_fetched_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
        data['_middleware_url'] = MIDDLEWARE_BASE_URL
        return jsonify(data), resp.status_code
    except http_requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'middleware_unreachable',
            'message': f'无法连接到中转站 {MIDDLEWARE_BASE_URL}，请确认中转站已启动',
            'middleware_url': MIDDLEWARE_BASE_URL
        }), 503
    except Exception as e:
        return jsonify({'error': str(e), 'middleware_url': MIDDLEWARE_BASE_URL}), 503

@app.route('/api/v2/floor_pulse/events')
def proxy_floor_pulse_events():
    """代理拉取中转站增量事件"""
    after_event_id = request.args.get('afterEventId', '0')
    try:
        resp = http_requests.get(
            f'{MIDDLEWARE_BASE_URL}/api/ue/events',
            params={'afterEventId': after_event_id},
            timeout=5
        )
        data = resp.json()
        
        # 注入 Mock 事件
        if _fp_mock_enabled:
            try:
                after_id = int(after_event_id)
                new_mocks = [e for e in _fp_mock_events if e["eventId"] > after_id]
                if new_mocks:
                    if "items" not in data: data["items"] = []
                    data["items"].extend(new_mocks)
                    data["items"].sort(key=lambda x: x["eventId"])
                    data["isLive"] = True
                    data["queryRange"] = { "afterEventId": after_id, "latestEventId": _fp_mock_event_id }
            except:
                pass

        return jsonify(data), resp.status_code
    except http_requests.exceptions.ConnectionError:
        return jsonify({'error': 'middleware_unreachable'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 503

@app.route('/api/v2/floor_pulse/health')
def proxy_floor_pulse_health():
    """代理查询中转站健康状态"""
    try:
        resp = http_requests.get(f'{MIDDLEWARE_BASE_URL}/health', timeout=3)
        return jsonify(resp.json()), resp.status_code
    except Exception:
        return jsonify({'status': 'unreachable'}), 503


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
# 动态图谱数据：CSV 导入 / API 代理
# ═══════════════════════════════════════════════════════════════

# 内存缓存：最近一次通过 CSV 或 API 导入的自定义图谱数据
_custom_graph_data = None

# 数据集列表：第一个元素永远是内置 Demo
_datasets = [
    {
        "id": "demo",
        "name": "标准实践（内置 Demo）",
        "created_at": "built-in",
        "node_count": None,   # 延迟卡，初始化时填充
        "link_count": None,
        "graph_data": None    # None 表示使用 get_graph_data 的硬标编 Demo
    }
]
# 当前激活的数据集 ID
_active_dataset_id = "demo"


@app.route('/api/v2/ontology/import_csv', methods=['POST'])
def import_csv_ontology():
    """
    接收前端上传的多个 CSV 文件，解析为图谱结构并缓存。
    前端通过 FormData 上传，每个 file input 的 name 就是文件名。
    """
    global _custom_graph_data

    if not request.files:
        return jsonify({"error": "未检测到任何上传文件"}), 400

    # 将 FileStorage 转为 { filename: str_content }
    file_dict = {}
    for key, fs in request.files.items():
        filename = fs.filename.lower().strip()
        content = fs.read().decode('utf-8-sig')  # 兼容 BOM
        file_dict[filename] = content

    # 严格校验必须文件
    missing = validate_files(file_dict)
    if missing:
        return jsonify({
            "error": f"缺少必须的文件: {', '.join(missing)}。请补充后重新上传。",
            "missing_files": missing
        }), 400

    try:
        graph = parse_ontology_csvs(file_dict)
        _custom_graph_data = graph
        return jsonify({
            "status": "ok",
            "node_count": len(graph["nodes"]),
            "link_count": len(graph["links"]),
            "category_count": len(graph["categories"]),
            "graph_data": graph
        })
    except Exception as e:
        return jsonify({"error": f"CSV 解析失败: {str(e)}"}), 500


@app.route('/api/v2/ontology/fetch_api', methods=['POST'])
def fetch_api_ontology():
    """
    代理拉取外部图数据库 API。
    Body: { "url": str, "token": str (可选) }
    期望目标 API 直接返回 { nodes: [...], links: [...], categories: [...] } 结构。
    """
    global _custom_graph_data

    data = request.json or {}
    url = data.get("url", "").strip()
    token = data.get("token", "").strip()

    if not url:
        return jsonify({"error": "请提供数据源 URL"}), 400

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = http_requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        graph = resp.json()

        # 基础格式校验
        if "nodes" not in graph or "links" not in graph:
            return jsonify({"error": "API 返回数据缺少 nodes 或 links 字段，不符合图谱格式要求"}), 422

        if "categories" not in graph:
            cat_set = set(n.get("category", "Core") for n in graph["nodes"])
            graph["categories"] = [{"name": c} for c in sorted(cat_set)]

        _custom_graph_data = graph
        return jsonify({
            "status": "ok",
            "node_count": len(graph["nodes"]),
            "link_count": len(graph["links"]),
            "category_count": len(graph["categories"]),
            "graph_data": graph
        })
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "连接超时，请检查 URL 是否可达"}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": "无法连接到目标地址，请检查网络或 URL"}), 502
    except Exception as e:
        return jsonify({"error": f"拉取失败: {str(e)}"}), 500


@app.route('/api/v2/ontology/custom_graph', methods=['GET'])
def get_custom_graph():
    """获取最近一次导入的自定义图谱数据（如果有）"""
    if _custom_graph_data is None:
        return jsonify({"error": "尚未导入任何自定义数据"}), 404
    return jsonify(_custom_graph_data)


@app.route('/api/v2/ontology/datasets', methods=['GET'])
def list_datasets():
    """获取所有已保存的数据集列表，包含内置 Demo"""
    result = []
    for ds in _datasets:
        result.append({
            "id": ds["id"],
            "name": ds["name"],
            "created_at": ds["created_at"],
            "node_count": ds["node_count"],
            "link_count": ds["link_count"],
            "is_active": ds["id"] == _active_dataset_id
        })
    return jsonify(result)


@app.route('/api/v2/ontology/datasets', methods=['POST'])
def create_empty_dataset():
    """
    新建空数据集（M0 — 为 2.9.2 提供合并目标）。
    Body: { "name": str, "activate": bool (默认 false) }
    """
    global _datasets, _active_dataset_id, _object_types

    import datetime
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "请提供数据集名称"}), 400

    # 重名检测（PRD § 10.2 漏洞 11）
    if any(ds["name"] == name for ds in _datasets):
        return jsonify({
            "error": "name_duplicated",
            "message": f"已存在同名数据集: {name}",
            "existing": [{"id": ds["id"], "name": ds["name"]}
                         for ds in _datasets if ds["name"] == name]
        }), 409

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # 用毫秒级时间戳，避免同一秒内创建造成 id 冲突
    ds_id = f"ds_{int(datetime.datetime.now().timestamp() * 1000)}"
    # 极端情况下仍冲突，加后缀确保唯一
    existing_ids = {d["id"] for d in _datasets}
    if ds_id in existing_ids:
        suffix = 1
        while f"{ds_id}_{suffix}" in existing_ids:
            suffix += 1
        ds_id = f"{ds_id}_{suffix}"

    new_ds = {
        "id": ds_id,
        "name": name,
        "created_at": created_at,
        "node_count": 0,
        "link_count": 0,
        "graph_data": {"nodes": [], "links": [], "categories": []}
    }
    _datasets.append(new_ds)

    activated = False
    if data.get("activate"):
        _active_dataset_id = ds_id
        _object_types = _project_dataset_to_object_types(new_ds)  # 空集 → {}
        activated = True

    return jsonify({
        "status": "ok",
        "dataset_id": ds_id,
        "name": name,
        "activated": activated
    })


@app.route('/api/v2/ontology/publish', methods=['POST'])
def publish_custom_graph():
    """将当前导入的自定义数据作为新数据集追加到列表。不再视口第一个元素。"""
    global _custom_graph_data, _datasets
    if not _custom_graph_data:
        return jsonify({"error": "没有可发布的数据，请先从 CSV 或 API 导入"}), 400

    import datetime
    data = request.json or {}
    name = data.get("name", "").strip() or "自定义数据集"
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ds_id = f"ds_{int(datetime.datetime.now().timestamp())}"

    new_ds = {
        "id": ds_id,
        "name": name,
        "created_at": created_at,
        "node_count": len(_custom_graph_data["nodes"]),
        "link_count": len(_custom_graph_data["links"]),
        "graph_data": _custom_graph_data
    }
    _datasets.append(new_ds)
    return jsonify({"status": "ok", "dataset_id": ds_id, "name": name})


def _project_dataset_to_object_types(ds):
    """
    把数据集 ds 投影为 _object_types 字典并返回（不写全局，让调用方决定）。
    PRD 2.9.2 § "node 自带字段优先 fallback old/默认" 规则。
    """
    # Demo / 内置 Demo（graph_data is None）→ 用 OBJECT_TYPES 常量
    if ds.get("id") == "demo" or ds.get("graph_data") is None:
        return {k: dict(v) for k, v in OBJECT_TYPES.items()}

    new_types = {}
    for node in ds["graph_data"].get("nodes", []):
        rid = node.get("rid")
        if not rid:
            continue
        old = _object_types.get(rid, {})  # 同名 rid 的现有定义（如果有）
        new_types[rid] = {
            "rid": rid,
            "name":        node.get("name", rid),
            "category":    node.get("category", "Core"),
            "description": node.get("description", ""),
            # ↓ 4 行修复：node 自带字段优先，fallback 到 old / 默认值
            "color":               node.get("color")               or old.get("color", "#888888"),
            "properties":          node.get("properties", []),
            "injected_interfaces": node.get("injected_interfaces") or old.get("injected_interfaces", []),
            "asset_id":            node.get("asset_id")            if node.get("asset_id") is not None else old.get("asset_id"),
            "mock_instances":      node.get("mock_instances", [])  or old.get("mock_instances", []),
            "source":              node.get("source"),  # 2.9.2 新增字段
        }
    return new_types


def _detect_dangling_refs(removed_or_overwritten_rids):
    """
    检测 InstanceStore 中是否有实例引用了即将被移除或覆盖的 rid。
    返回 [{rid, instance_count, instance_ids:[最多5个示例]}]
    """
    if not removed_or_overwritten_rids:
        return []
    rid_set = set(removed_or_overwritten_rids)
    counter = {}
    for iid, inst in instance_store._instances.items():
        rid = inst.get("object_type_rid")
        if rid in rid_set:
            counter.setdefault(rid, []).append(iid)
    return [
        {"rid": rid, "instance_count": len(ids), "instance_ids": ids[:5]}
        for rid, ids in counter.items()
    ]


@app.route('/api/v2/ontology/datasets/activate', methods=['POST'])
def activate_dataset():
    """
    激活指定数据集，同时将该数据集的节点写入 _object_types。
    Body: { "dataset_id": str }
    """
    global _active_dataset_id, _object_types
    data = request.json or {}
    ds_id = data.get("dataset_id", "").strip()
    if not ds_id:
        return jsonify({"error": "请提供 dataset_id"}), 400

    ds = next((d for d in _datasets if d["id"] == ds_id), None)
    if not ds:
        return jsonify({"error": f"找不到数据集: {ds_id}"}), 404

    _active_dataset_id = ds_id
    _object_types = _project_dataset_to_object_types(ds)
    return jsonify({"status": "ok", "active": _active_dataset_id})


@app.route('/api/v2/ontology/datasets/<ds_id>/graph', methods=['GET'])
def get_dataset_graph(ds_id):
    """获取指定数据集的图谱数据（用于前端预览）"""
    ds = next((d for d in _datasets if d["id"] == ds_id), None)
    if not ds:
        return jsonify({"error": f"找不到数据集: {ds_id}"}), 404
    if ds.get("graph_data") is None:
        # Demo 数据集，重定向到 graph_data
        return get_graph_data()
    return jsonify(ds["graph_data"])


@app.route('/api/v2/ontology/datasets/<ds_id>', methods=['DELETE'])
def delete_dataset(ds_id):
    """删除指定的数据集，如果删除的是当前激活的，则退回至 Demo"""
    global _datasets, _active_dataset_id, _object_types
    if ds_id == "demo":
        return jsonify({"error": "内置数据集无法删除"}), 400

    ds_index = next((i for i, d in enumerate(_datasets) if d["id"] == ds_id), None)
    if ds_index is None:
        return jsonify({"error": f"找不到数据集: {ds_id}"}), 404

    _datasets.pop(ds_index)

    # 如果删除的是当前激活项，重置为 demo
    if _active_dataset_id == ds_id:
        _active_dataset_id = "demo"
        _object_types = {k: dict(v) for k, v in OBJECT_TYPES.items()}

    return jsonify({"status": "ok", "active": _active_dataset_id})


# ═══════════════════════════════════════════════════════════════
# CAD 自动化生成 API (DXF -> JSON)
# ═══════════════════════════════════════════════════════════════

# 服务端内存缓存：最近一次解析结果（供 UE5 通过 HTTP 拉取）
_cad_latest_result = None
_cad_latest_filename = None
_cad_latest_timestamp = None

@app.route('/api/v2/cad/parse', methods=['POST'])
def parse_cad_dxf():
    global _cad_latest_result, _cad_latest_filename, _cad_latest_timestamp

    if 'file' not in request.files:
        return jsonify({"error": "未检测到上传文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400

    if not file.filename.lower().endswith('.dxf'):
        return jsonify({"error": "仅支持 .dxf 文件格式。原生 DWG 请先用 CAD 等工具另存为 DXF"}), 400

    try:
        import parser_dxf
        import tempfile
        import datetime

        _, temp_path = tempfile.mkstemp(suffix='.dxf')
        file.save(temp_path)

        wall_height = float(request.form.get('wall_height', 4500.0))
        wall_thickness = float(request.form.get('wall_thickness', 240.0))

        result_json = parser_dxf.parse_dxf_to_json(
            temp_path, 
            wall_height=wall_height, 
            wall_thickness=wall_thickness
        )
        os.remove(temp_path)

        if result_json is None:
            return jsonify({"error": "解析 DXF 文件失败，可能文件损坏或格式不支持"}), 500

        # ── 缓存到后端内存，供 UE5 拉取 ─────────────────────────────
        _cad_latest_result = result_json
        _cad_latest_filename = file.filename
        _cad_latest_timestamp = datetime.datetime.now().isoformat()

        # 给响应加入元信息，方便前端展示
        result_json["_meta"] = {
            "source_file": file.filename,
            "parsed_at": _cad_latest_timestamp,
            "pull_url": "/api/v2/cad/latest"
        }

        return jsonify(result_json)

    except Exception as e:
        return jsonify({"error": f"解析失败: {str(e)}"}), 500


@app.route('/api/v2/cad/latest', methods=['GET'])
def get_cad_latest():
    """
    获取最近一次解析的 CAD JSON 数据。
    UE5 端配置该 URL 后即可直接 HTTP GET 拉取，无需本地文件路径。
    返回格式与 /api/v2/cad/parse 完全一致。
    """
    if _cad_latest_result is None:
        return jsonify({"error": "尚未上传并解析任何 DXF 图纸"}), 404
    return jsonify(_cad_latest_result)


@app.route('/api/v2/cad/status', methods=['GET'])
def get_cad_status():
    """返回当前缓存状态（文件名、时间、实体数量），供前端轮询确认。"""
    if _cad_latest_result is None:
        return jsonify({"has_data": False})

    entities = _cad_latest_result.get("entities", [])
    wall_count = sum(1 for e in entities if e.get("generate_type") == "PROCEDURAL_WALL")
    col_count = sum(1 for e in entities if e.get("generate_type") == "INSTANCE")

    return jsonify({
        "has_data": True,
        "source_file": _cad_latest_filename,
        "parsed_at": _cad_latest_timestamp,
        "entity_count": len(entities),
        "wall_count": wall_count,
        "column_count": col_count,
        "pull_url": "/api/v2/cad/latest"
    })


# ═══════════════════════════════════════════════════════════════
# 知识图谱 Mock 数据（ontology_graph.html 用）
# ═══════════════════════════════════════════════════════════════

@app.route('/api/v2/ontology/graph_data', methods=['GET'])
def get_graph_data():
    # 此接口将始终只返回内置 Demo 数据，不受发布数据集影响
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



# ============ OntoTwin Lite 模块（新增，不影响现有路由）============
try:
    from lite.models.db import init_db
    from lite.api import register_lite_routes
    init_db()
    register_lite_routes(app)
except Exception as _lite_err:
    print(f"[Lite] 模块加载失败: {_lite_err}")
# ================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
