"""
ontology_parser.py
==================
将图数据库导出的 6 张 CSV 表解析为前端 ECharts 可直接渲染的
{ nodes, links, categories } JSON 结构。

必须文件（缺一则报错）:
  - objectdef.csv        对象类型定义
  - linkdef.csv          关系定义
  - linksourcetype.csv   关系起点类型
  - linktargettype.csv   关系终点类型

可选文件（缺失时不影响图谱骨架）:
  - propertydef.csv      属性定义
  - hasproperty.csv      对象与属性的映射
"""

import csv
import io
import json

# ── 必须存在的文件白名单 ──────────────────────────────────
REQUIRED_FILES = {"objectdef.csv", "linkdef.csv", "linksourcetype.csv", "linktargettype.csv"}
OPTIONAL_FILES = {"propertydef.csv", "hasproperty.csv"}

# ── 自动分类配色（覆盖默认） ──────────────────────────────
# 根据关键词自动划分 category，用于图谱着色
_CATEGORY_KEYWORDS = {
    "Equipment":   ["equipment", "ledger", "设备"],
    "Material":    ["material", "md_material", "物料", "stock", "bw_stock"],
    "Method":      ["operation", "sorting", "plan", "delivery", "工序", "计划", "配套", "配送", "日计划", "daily"],
    "Personnel":   ["user", "人员", "obj_user"],
    "Environment": ["warehouse", "location", "station", "库位", "站位", "库房", "仓库"],
    "Event":       ["failure", "fault", "故障"],
    "Core":        ["model", "机型", "dispatch", "派工", "batch", "批次", "sortie", "架次", "department", "部门"],
}


def _guess_category(rid: str, display_name: str) -> str:
    """根据 RID 和显示名自动猜测分类"""
    combined = (rid + " " + display_name).lower()
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                return cat
    return "Core"


def _read_csv(file_content: str) -> list:
    """将 CSV 字符串解析为 list[dict]"""
    reader = csv.DictReader(io.StringIO(file_content))
    return list(reader)


def validate_files(file_dict: dict) -> list:
    """
    校验上传的文件集合，返回缺失的必须文件名列表。
    file_dict: { "objectdef.csv": <str_content>, ... }
    """
    missing = []
    for name in REQUIRED_FILES:
        if name not in file_dict or not file_dict[name].strip():
            missing.append(name)
    return missing


def parse_ontology_csvs(file_dict: dict) -> dict:
    """
    核心解析入口。

    参数:
        file_dict: { "filename.csv": "csv_string_content", ... }

    返回:
        {
            "nodes": [...],
            "links": [...],
            "categories": [...]
        }
    """

    # ── 1. 解析 objectdef.csv → 节点 ──────────────────────
    objects_raw = _read_csv(file_dict["objectdef.csv"])
    nodes_by_rid = {}
    for obj in objects_raw:
        rid = obj.get("rid", "").strip()
        if not rid:
            continue
        display_name = obj.get("display_name", rid)
        category = _guess_category(rid, display_name)
        nodes_by_rid[rid] = {
            "id": rid,
            "name": display_name,
            "category": category,
            "symbolSize": 35 if category in ("Core", "Method") else 30,
            "rid": rid,
            "api_name": obj.get("api_name", rid),
            "display_name": display_name,
            "description": obj.get("description", ""),
            "lifecycle_status": obj.get("lifecycle_status", "ACTIVE"),
            "primary_keys": _parse_json_field(obj.get("primary_key_property_rids", "[]")),
            "validation": _parse_json_field(obj.get("validation_expressions", "[]")),
            "read_path": obj.get("read_asset_path", ""),
            "properties": [],            # 稍后填充
            "capabilities": [],           # 三维能力插槽（预留）
        }

    # ── 2. 解析 propertydef.csv → 属性字典 ────────────────
    prop_dict = {}
    if "propertydef.csv" in file_dict and file_dict["propertydef.csv"].strip():
        props_raw = _read_csv(file_dict["propertydef.csv"])
        for p in props_raw:
            p_rid = p.get("rid", "").strip()
            if not p_rid:
                continue
            prop_dict[p_rid] = {
                "rid": p_rid,
                "name": p.get("api_name", p_rid),
                "label": p.get("display_name", p_rid),
                "type": p.get("data_type", "STRING"),
                "description": p.get("description", ""),
                "physical_column": p.get("physical_column", ""),
            }

    # ── 3. 解析 hasproperty.csv → 将属性挂到节点上 ────────
    if "hasproperty.csv" in file_dict and file_dict["hasproperty.csv"].strip():
        hp_raw = _read_csv(file_dict["hasproperty.csv"])
        for row in hp_raw:
            obj_rid = row.get("from_rid", "").strip()
            prop_rid = row.get("to_rid", "").strip()
            if obj_rid in nodes_by_rid and prop_rid in prop_dict:
                nodes_by_rid[obj_rid]["properties"].append(prop_dict[prop_rid])

    # ── 4. 解析 linkdef + source/target → 边 ─────────────
    links_raw = _read_csv(file_dict["linkdef.csv"])
    source_raw = _read_csv(file_dict["linksourcetype.csv"])
    target_raw = _read_csv(file_dict["linktargettype.csv"])

    # 建立 link_rid → source_type / target_type 的映射
    source_map = {}
    for row in source_raw:
        link_rid = row.get("from_rid", "").strip()
        src_type = row.get("to_rid", "").strip()
        if link_rid and src_type:
            source_map[link_rid] = src_type

    target_map = {}
    for row in target_raw:
        link_rid = row.get("from_rid", "").strip()
        tgt_type = row.get("to_rid", "").strip()
        if link_rid and tgt_type:
            target_map[link_rid] = tgt_type

    links = []
    for link in links_raw:
        link_rid = link.get("rid", "").strip()
        if not link_rid:
            continue
        source_type = source_map.get(link_rid)
        target_type = target_map.get(link_rid)
        if not source_type or not target_type:
            continue
        # 确保源和目标节点都存在（可能在 objectdef 中未收录引用节点）
        if source_type not in nodes_by_rid or target_type not in nodes_by_rid:
            continue
        links.append({
            "source": source_type,
            "target": target_type,
            "label": link.get("display_name", link_rid),
            "rid": link_rid,
            "description": link.get("description", ""),
            "cardinality": link.get("cardinality", ""),
        })

    # ── 5. 收集所有出现过的 category → categories 数组 ────
    cat_set = set()
    for n in nodes_by_rid.values():
        cat_set.add(n["category"])
    categories = [{"name": c} for c in sorted(cat_set)]

    nodes = list(nodes_by_rid.values())

    return {
        "nodes": nodes,
        "links": links,
        "categories": categories,
    }


def _parse_json_field(val: str) -> list:
    """安全解析可能是 JSON 数组的字符串字段"""
    if not val or not val.strip():
        return []
    try:
        result = json.loads(val)
        if isinstance(result, list):
            return result
        return [result]
    except (json.JSONDecodeError, TypeError):
        return []
