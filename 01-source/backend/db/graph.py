"""
Neo4j 连接层（OntoTwin 3.4 —— 本体图库读取）
============================================================
本体（语义层）唯一真源在 Neo4j（由 tools/lingshu 工具链灌入，见
ontology_registry/）。本模块只做**读**：运行时 API 对本体是只读的，
写入永远走「本体 JSON → generate_ontology_cypher.py → cypher-shell」链路，
保证图内容始终可由 git 里的 registry 文档重建。

连接配置走环境变量（docker-compose 已注入）：
    NEO4J_URI       默认 bolt://localhost:7687（本地直跑）
    NEO4J_USER      默认 neo4j
    NEO4J_PASSWORD  默认 ontotwin123

图库不可达时调用方应降级（如 API 返回 503），不影响 Nexus 主功能。
"""

import os

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "ontotwin123")

_driver = None


def get_driver():
    """进程内单例 driver（driver 自带连接池，惰性创建）。"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def ping():
    """连通性自检：True = 图库可达。"""
    try:
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


def fetch_registry():
    """
    读本体注册表：接口（含继承与必需属性）+ 对象类型（含实现接口与 x_ 扩展属性）。
    返回 {"interfaces": [...], "object_types": [...]}，字段名与图节点属性一致。
    """
    q_interfaces = """
    MATCH (i:InterfaceType)
    OPTIONAL MATCH (i)-[:EXTENDS]->(p:InterfaceType)
    OPTIONAL MATCH (i)-[:REQUIRES]->(s:SharedPropertyType)
    RETURN i.rid AS rid, i.api_name AS api_name, i.display_name AS display_name,
           i.lifecycle_status AS lifecycle_status,
           collect(DISTINCT p.rid) AS extends,
           collect(DISTINCT {rid: s.rid, api_name: s.api_name,
                             display_name: s.display_name, data_type: s.data_type}) AS requires
    ORDER BY api_name
    """
    q_object_types = """
    MATCH (o:ObjectType)
    OPTIONAL MATCH (o)-[:IMPLEMENTS]->(i:InterfaceType)
    RETURN o.rid AS rid, o.api_name AS api_name, o.display_name AS display_name,
           o.lifecycle_status AS lifecycle_status,
           o.x_block_name AS x_block_name, o.x_source AS x_source,
           collect(DISTINCT i.api_name) AS implements
    ORDER BY api_name
    """
    with get_driver().session() as session:
        interfaces = [dict(r) for r in session.run(q_interfaces)]
        object_types = [dict(r) for r in session.run(q_object_types)]

    # OPTIONAL MATCH 无命中时 collect 会产出 null 占位条目 → 过滤掉
    for i in interfaces:
        i["extends"] = [e for e in i["extends"] if e]
        i["requires"] = [r for r in i["requires"] if r.get("rid")]
    for o in object_types:
        o["implements"] = [x for x in o["implements"] if x]
    return {"interfaces": interfaces, "object_types": object_types}


def fetch_graph_echarts():
    """
    本体图库 → ECharts {nodes, links, categories}（与 ontology_parser 输出同构，
    前端 renderCustomGraph / 数据集发布链路零改动复用）。
    节点：对象类型 + 接口 + 共享属性；边：实现接口 / 接口继承 / 接口要求属性。
    """
    reg = fetch_registry()

    # 共享属性节点也进图（数量小、能直观展示"接口→属性"契约层）
    q_shared = """
    MATCH (s:SharedPropertyType)
    RETURN s.rid AS rid, s.api_name AS api_name, s.display_name AS display_name,
           s.data_type AS data_type, s.description AS description
    ORDER BY api_name
    """
    with get_driver().session() as session:
        shared = [dict(r) for r in session.run(q_shared)]

    def _node(rid, name, category, size, extra=None):
        n = {
            "id": rid, "name": name, "category": category, "symbolSize": size,
            "rid": rid, "display_name": name,
            "api_name": "", "description": "", "lifecycle_status": "ACTIVE",
            "primary_keys": [], "validation": [], "read_path": "",
            "properties": [], "capabilities": [],
        }
        n.update(extra or {})
        return n

    nodes, links = [], []

    for i in reg["interfaces"]:
        nodes.append(_node(i["rid"], i["display_name"], "能力接口", 40, {
            "api_name": i["api_name"], "lifecycle_status": i["lifecycle_status"],
            "properties": [
                {"rid": r["rid"], "name": r["api_name"], "label": r.get("display_name", r["api_name"]),
                 "type": r.get("data_type", ""), "description": ""}
                for r in i["requires"]
            ],
        }))
        for parent_rid in i["extends"]:
            links.append({"source": i["rid"], "target": parent_rid,
                          "label": "继承", "rid": f"{i['rid']}:extends",
                          "description": "接口继承", "cardinality": ""})
        for r in i["requires"]:
            links.append({"source": i["rid"], "target": r["rid"],
                          "label": "要求属性", "rid": f"{i['rid']}:req:{r['rid']}",
                          "description": "接口要求的共享属性", "cardinality": ""})

    iface_name_to_rid = {i["api_name"]: i["rid"] for i in reg["interfaces"]}
    for o in reg["object_types"]:
        nodes.append(_node(o["rid"], o["display_name"], "对象类型", 32, {
            "api_name": o["api_name"], "lifecycle_status": o["lifecycle_status"],
            "description": f"块名: {o.get('x_block_name') or ''} | 来源: {o.get('x_source') or ''}".strip(" |"),
        }))
        for impl in o["implements"]:
            target = iface_name_to_rid.get(impl)
            if target:
                links.append({"source": o["rid"], "target": target,
                              "label": "实现", "rid": f"{o['rid']}:impl:{target}",
                              "description": "类型实现能力接口", "cardinality": ""})

    for s in shared:
        nodes.append(_node(s["rid"], s["display_name"], "共享属性", 18, {
            "api_name": s["api_name"], "description": s.get("description") or "",
        }))

    categories = [{"name": c} for c in ("对象类型", "能力接口", "共享属性")]
    return {"nodes": nodes, "links": links, "categories": categories}
