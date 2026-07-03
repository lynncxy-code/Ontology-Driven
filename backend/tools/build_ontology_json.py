"""
build_ontology_json.py —— OntoTwin 本体 → 灵枢 registry JSON 转换器（3.4）
============================================================
读当前激活项目的 object_types + mapping_store 的 I3D 接口定义，
生成符合 tools/lingshu/ontology.schema.json 的本体 registry 文档，
供 vendored 的 generate_ontology_cypher.py 校验并生成 Cypher 灌入 Neo4j。

身份稳定性（关键约定）：
  * RID 首次生成 UUID 后写进输出文件并进 git，**永不重新生成**；
  * 重跑时按 api_name 对齐已有条目、保留其 rid（幂等）——所以输出文件
    ontology_registry/ontotwin.ontology.json 必须提交进版本库。

同时生成 ontotwin_extensions.cypher：给 ObjectType 节点补 OntoTwin 扩展属性
（x_block_name / x_source，x_ 前缀=扩展字段；官方生成器 SET += 不会删它们）。

运行（backend 容器内或 backend 目录下）：
    python -m tools.build_ontology_json
"""

import json
import os
import re
import sys
import uuid
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mapping_store import INTERFACES  # noqa: E402  两层 I3D 接口定义（stdlib-only，安全导入）

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REGISTRY_DIR = os.path.join(_BACKEND, "ontology_registry")


def _out_paths(pid):
    """registry 按项目分文件——不同项目的类型身份互不覆盖（RID 一次生成永不重发）。"""
    return (os.path.join(_REGISTRY_DIR, f"ontotwin.{pid}.ontology.json"),
            os.path.join(_REGISTRY_DIR, f"ontotwin.{pid}.extensions.cypher"))

API_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")

# mapping_store 属性类型 → registry DataType
_DT = {"string": "DT_STRING", "boolean": "DT_BOOLEAN", "number": "DT_DOUBLE", "enum": "DT_STRING"}


def _api_name(raw, used, fallback_prefix="t"):
    """任意名字 → 合法唯一 api_name（中文/非法字符退化为前缀+哈希）。"""
    slug = re.sub(r"[^a-z0-9]+", "_", str(raw).lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not API_NAME_RE.match(slug):
        slug = f"{fallback_prefix}_{hashlib.md5(str(raw).encode('utf-8')).hexdigest()[:8]}"
    base, n = slug, 2
    while slug in used:
        slug = f"{base}_{n}"
        n += 1
    used.add(slug)
    return slug


def _load_active_project():
    """经 ProjectStore 读激活项目（跟随 ONTOTWIN_STORE，勿直读 JSON 文件——
    否则默认切 PG 后会读到过期数据，重蹈 migrate 硬编码 PG 的双真源劈叉）。"""
    from project_store import ProjectStore
    store = ProjectStore()
    proj = store.get_active()
    if proj is None:
        raise SystemExit("当前无激活项目")
    print(f"存储后端={store.__class__.__name__} | 项目={store.get_active_id()}（{proj.get('name')}）")
    return proj["id"], proj


def _load_existing(out_json):
    if os.path.exists(out_json):
        with open(out_json, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _index_by_api_name(section):
    return {v.get("api_name"): v for v in (section or {}).values() if isinstance(v, dict)}


def _rid(prefix, existing_entry):
    """已有条目复用 rid（身份稳定）；否则新发 UUID。"""
    if existing_entry and isinstance(existing_entry.get("rid"), str):
        return existing_entry["rid"]
    return f"{prefix}{uuid.uuid4()}"


def build():
    pid, proj = _load_active_project()
    out_json, out_ext = _out_paths(pid)
    prev = _load_existing(out_json)
    prev_shared = _index_by_api_name(prev.get("shared_property_types"))
    prev_iface = _index_by_api_name(prev.get("interface_types"))
    prev_obj = _index_by_api_name(prev.get("object_types"))

    used_api = set()

    # ── 1. shared_property_types：instance_id + 各接口属性（按 name 去重）────
    shared = {}                     # rid → def
    shared_rid_by_name = {}         # 属性名 → rid
    def add_shared(name, label, dtype):
        api = name if API_NAME_RE.match(name) else _api_name(name, set())
        old = prev_shared.get(api)
        rid = _rid("ri.shprop.", old)
        shared[rid] = {
            "rid": rid, "api_name": api, "display_name": label or name,
            "description": "OntoTwin 三维接口共享属性",
            "lifecycle_status": "ACTIVE", "data_type": dtype,
        }
        shared_rid_by_name[name] = rid

    add_shared("instance_id", "实例身份证号", "DT_STRING")
    for iface in INTERFACES:
        for p in iface.get("properties", []):
            if p["name"] not in shared_rid_by_name:
                add_shared(p["name"], p.get("label"), _DT.get(p.get("type"), "DT_STRING"))

    # ── 2. interface_types：I3D_Representable + 3 子接口（EXTENDS 父）───────
    ifaces = {}
    iface_rid_by_name = {}          # I3D_xxx → rid
    iface_required = {}             # rid → [shared rid]（仅自身声明，不含继承）
    parent_name = next(i["rid"] for i in INTERFACES if i.get("tier") == "parent")
    for spec in INTERFACES:
        api = _api_name(spec["rid"], used_api, "iface")
        old = prev_iface.get(api)
        rid = _rid("ri.iface.", old)
        required = [shared_rid_by_name[p["name"]] for p in spec.get("properties", [])]
        entry = {
            "rid": rid, "api_name": api, "display_name": spec.get("label", spec["rid"]),
            "description": spec.get("description", ""),
            "lifecycle_status": "ACTIVE", "category": "OBJECT_INTERFACE",
            "required_shared_property_type_rids": required,
        }
        ifaces[rid] = entry
        iface_rid_by_name[spec["rid"]] = rid
        iface_required[rid] = required
    # 子接口 extends 父接口
    parent_rid = iface_rid_by_name[parent_name]
    for spec in INTERFACES:
        if spec.get("tier") == "child":
            ifaces[iface_rid_by_name[spec["rid"]]]["extends_interface_type_rids"] = [parent_rid]

    def required_transitive(iface_rids):
        """实现这些接口需要的全部共享属性（含 EXTENDS 继承）。"""
        result, seen = [], set()
        def visit(rid):
            if rid in seen or rid not in ifaces:
                return
            seen.add(rid)
            for parent in ifaces[rid].get("extends_interface_type_rids", []):
                visit(parent)
            for sp in iface_required.get(rid, []):
                if sp not in result:
                    result.append(sp)
        for r in iface_rids:
            visit(r)
        return result

    # ── 3. object_types：当前项目全部类型 ──────────────────────────────────
    objects = {}
    ext_lines = []                  # 扩展属性 Cypher
    for ot_rid_raw, ot in (proj.get("object_types") or {}).items():
        name = ot.get("name") or ot_rid_raw
        api = _api_name(ot_rid_raw, used_api, "obj")
        old = prev_obj.get(api)
        rid = _rid("ri.obj.", old)
        source = ot.get("source") or "ontotwin"
        implements = [iface_rid_by_name[i] for i in (ot.get("injected_interfaces") or [])
                      if i in iface_rid_by_name]

        # 属性：instance_id(主键) + 实现接口要求的全部共享属性（含继承）
        old_props = (old or {}).get("property_types") or {}
        props, pk_rids = {}, []
        needed = [shared_rid_by_name["instance_id"]] + [
            sp for sp in required_transitive(implements)
            if sp != shared_rid_by_name["instance_id"]
        ]
        for sp_rid in needed:
            sp = shared[sp_rid]
            p_api = sp["api_name"]
            p_rid = _rid("ri.prop.", old_props.get(p_api))
            props[p_api] = {
                "rid": p_rid, "api_name": p_api, "display_name": sp["display_name"],
                "lifecycle_status": "ACTIVE", "data_type": sp["data_type"],
                "inherit_from_shared_property_type_rid": sp_rid,
            }
            if p_api == "instance_id":
                pk_rids.append(p_rid)

        objects[rid] = {
            "rid": rid, "api_name": api, "display_name": name,
            "description": ot.get("description", "") or "",
            "lifecycle_status": "EXPERIMENTAL" if str(source).startswith("cad_auto") else "ACTIVE",
            "property_types": props,
            "implements_interface_type_rids": implements,
            "primary_key_property_type_rids": pk_rids,
        }
        # 扩展属性：块名（=原 rid）与来源，x_ 前缀不会被官方生成器冲掉
        ext_lines.append(
            'MATCH (n:ObjectType {rid: %s})\nSET n.x_block_name = %s, n.x_source = %s, n.x_origin = "ontotwin";'
            % (json.dumps(rid), json.dumps(ot_rid_raw, ensure_ascii=False),
               json.dumps(str(source), ensure_ascii=False))
        )

    registry = {
        "version": "ontotwin-3.4.0",
        "shared_property_types": shared,
        "interface_types": ifaces,
        "object_types": objects,
        "link_types": {},
        "action_types": {},
    }

    os.makedirs(_REGISTRY_DIR, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    with open(out_ext, "w", encoding="utf-8") as f:
        f.write("// OntoTwin 扩展属性（x_ 前缀）——官方生成器重灌不会覆盖\n\n")
        f.write("\n\n".join(ext_lines) + "\n")

    print(f"项目 {pid}: 共享属性 {len(shared)} | 接口 {len(ifaces)} | 类型 {len(objects)}")
    print(f"registry → {out_json}")
    print(f"扩展属性 → {out_ext}")


if __name__ == "__main__":
    build()
