"""
ProjectStorePG —— PostgreSQL 后端（OntoTwin 3.4）
============================================================
策略：继承 JSON 版 ProjectStore，**只覆盖 IO 原语**（读/写/激活/列举/删除），
所有内存逻辑（spawn / update_raw_state / mint_instances / 构件 / 帧 …）原样复用。

对外方法签名与 ProjectStore 完全一致（app.py 83 处调用不动）。
内存模型不变：self._current 仍是「当前激活项目」的完整 dict；只是它的
落盘/装载改成向 PG 分表(project/object_type/instance/zone) 拆解与重组。

启用：环境变量 ONTOTWIN_STORE=pg（见 project_store.py 底部开关）。
默认仍是 JSON 版，PG 为可选，互不影响。

⚠️ 需要一个可连的 PostgreSQL（docker compose 的 db 服务或本地 PG）。
"""

import time
import threading

from psycopg.types.json import Jsonb

from project_store import ProjectStore, _clean_hierarchy_path, _default_spatial_profile, apply_instance_metadata
from db import pg


class ProjectStorePG(ProjectStore):
    def __init__(self, *args, **kwargs):
        # 不调用父类 __init__（那是 JSON 目录初始化）；自建最小状态。
        self._lock = threading.RLock()
        self._active_id = None
        self._current = None
        self._dirty = False
        try:
            pg.init_schema()          # 幂等建表（docker 首次已建；本地/补建兜底）
        except Exception as e:
            print(f"[project_store_pg] init_schema 跳过: {e}")
        self._load_active()

    # ── 激活态 ───────────────────────────────────────────────
    def _load_active(self):
        self._active_id = None
        self._current = None
        try:
            with pg.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT v FROM app_singleton WHERE k='active_project_id'")
                    row = cur.fetchone()
                    if row and row[0]:
                        self._active_id = row[0]
            if self._active_id:
                self._current = self._read_project(self._active_id)
                if self._current is None:
                    self._active_id = None
        except Exception as e:
            # PG 不可用时不崩：保持无激活，app 仍能起（只是无数据）
            print(f"[project_store_pg] _load_active 失败(PG 不可用?): {e}")
            self._active_id = None
            self._current = None

    def _save_active(self):
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO app_singleton (k, v) VALUES ('active_project_id', %s)
                       ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v""",
                    (self._active_id,),
                )

    # ── 读单个项目：从分表重组成内存 dict ────────────────────
    def _read_project(self, pid):
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, name, created_at, dataset, calibration, spatial_profile,
                              components, instance_roster, frames
                       FROM project WHERE id = %s AND deleted_at IS NULL""",
                    (pid,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                proj = {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "dataset": row[3],
                    "calibration": row[4],
                    "spatial_profile": row[5],
                    "components": row[6] or {},
                    "instance_roster": row[7] or [],
                    "frames": row[8] or [],
                    "object_types": {},
                    "instances": {},
                }
                cur.execute(
                    "SELECT rid, data FROM object_type WHERE project_id = %s AND deleted_at IS NULL",
                    (pid,),
                )
                for rid, data in cur.fetchall():
                    proj["object_types"][rid] = data or {}

                cur.execute(
                    """SELECT id, object_type_rid, object_type_name, zone_id, component_id,
                              source, ext_guid, display_name, hierarchy_path,
                              source_folder_path, source_asset_path,
                              classification_status, classification_key,
                              status, created_at, last_seen,
                              render_config, raw_state
                       FROM instance WHERE project_id = %s AND deleted_at IS NULL""",
                    (pid,),
                )
                for r in cur.fetchall():
                    rec = {
                        "id": r[0],
                        "object_type_rid": r[1],
                        "object_type_name": r[2],
                        "display_name": r[7] or r[0],
                        "hierarchy_path": _clean_hierarchy_path(r[8], [r[2] or r[1] or "未分类"]),
                        "source_folder_path": r[9] or "",
                        "source_asset_path": r[10] or "",
                        "classification_status": r[11] or "confirmed",
                        "classification_key": r[12] or "",
                        "render_config": r[16] or {},
                        "created_at": r[14],
                        "last_seen": r[15],
                        "status": r[13],
                        "raw_state": r[17] or {},
                    }
                    # 可空的新增/绑定字段，有值才写回（保持记录形状与 JSON 版一致）
                    if r[3] is not None:
                        rec["zone_id"] = r[3]
                    if r[4] is not None:
                        rec["component_id"] = r[4]
                    if r[5] is not None:
                        rec["source"] = r[5]
                    if r[6] is not None:
                        rec["ext_guid"] = r[6]
                    apply_instance_metadata(rec)
                    proj["instances"][r[0]] = rec
                return self._ensure_collections(proj)

    # ── 存当前项目：把内存 dict 拆解写回分表（事务原子）────────
    def _save_current(self):
        if not self._current:
            return
        proj = self._current
        pid = proj["id"]
        ots = proj.get("object_types") or {}
        insts = proj.get("instances") or {}
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # 1) 项目行（低频嵌套块直接 JSONB）
                    cur.execute(
                        """INSERT INTO project
                             (id, name, created_at, dataset, calibration, spatial_profile,
                              components, instance_roster, frames, deleted_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, NULL)
                           ON CONFLICT (id) DO UPDATE SET
                             name=EXCLUDED.name, created_at=EXCLUDED.created_at,
                             dataset=EXCLUDED.dataset, calibration=EXCLUDED.calibration,
                             spatial_profile=EXCLUDED.spatial_profile,
                             components=EXCLUDED.components,
                             instance_roster=EXCLUDED.instance_roster,
                             frames=EXCLUDED.frames, deleted_at=NULL""",
                        (
                            pid, proj.get("name"), proj.get("created_at"),
                            Jsonb(proj.get("dataset")), Jsonb(proj.get("calibration")),
                            Jsonb(proj.get("spatial_profile")),
                            Jsonb(proj.get("components") or {}),
                            Jsonb(proj.get("instance_roster") or []),
                            Jsonb(proj.get("frames") or []),
                        ),
                    )

                    # 2) 本体：整表替换（set_object_types 语义即整体替换，量小）
                    cur.execute("DELETE FROM object_type WHERE project_id = %s", (pid,))
                    for rid, rec in ots.items():
                        rec = rec or {}
                        cur.execute(
                            """INSERT INTO object_type (project_id, rid, name, source, data)
                               VALUES (%s,%s,%s,%s,%s)""",
                            (pid, rid, rec.get("name"), rec.get("source"), Jsonb(rec)),
                        )

                    # 3) 实例：present upsert。
                    # 注意：普通项目保存可能只是在保存 components / frames / dataset，
                    # 不应把内存中暂时缺席的实例视为删除。明确删除语义由
                    # remove / clear_instances / mint_instances 覆盖实现。
                    for iid, rec in insts.items():
                        cur.execute(
                            """INSERT INTO instance
                                 (project_id, id, object_type_rid, object_type_name, zone_id,
                                  component_id, source, ext_guid,
                                  display_name, hierarchy_path, source_folder_path, source_asset_path,
                                  classification_status, classification_key,
                                  status, created_at, last_seen,
                                  render_config, raw_state, deleted_at)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NULL)
                               ON CONFLICT (project_id, id) DO UPDATE SET
                                 object_type_rid=EXCLUDED.object_type_rid,
                                 object_type_name=EXCLUDED.object_type_name,
                                 zone_id=EXCLUDED.zone_id, component_id=EXCLUDED.component_id,
                                 source=EXCLUDED.source, ext_guid=EXCLUDED.ext_guid,
                                 display_name=EXCLUDED.display_name,
                                 hierarchy_path=EXCLUDED.hierarchy_path,
                                 source_folder_path=EXCLUDED.source_folder_path,
                                 source_asset_path=EXCLUDED.source_asset_path,
                                 classification_status=EXCLUDED.classification_status,
                                 classification_key=EXCLUDED.classification_key,
                                 status=EXCLUDED.status, created_at=EXCLUDED.created_at,
                                 last_seen=EXCLUDED.last_seen,
                                 render_config=EXCLUDED.render_config,
                                 raw_state=EXCLUDED.raw_state, deleted_at=NULL""",
                            (
                                pid, iid, rec.get("object_type_rid"), rec.get("object_type_name"),
                                rec.get("zone_id"), rec.get("component_id"),
                                rec.get("source", "ontotwin"), rec.get("ext_guid"),
                                rec.get("display_name") or iid,
                                Jsonb(_clean_hierarchy_path(
                                    rec.get("hierarchy_path"),
                                    [rec.get("object_type_name") or rec.get("object_type_rid") or "未分类"],
                                )),
                                rec.get("source_folder_path") or "",
                                rec.get("source_asset_path") or "",
                                rec.get("classification_status") or "confirmed",
                                rec.get("classification_key") or "",
                                rec.get("status", "online"), rec.get("created_at"),
                                rec.get("last_seen"),
                                Jsonb(rec.get("render_config") or {}),
                                Jsonb(rec.get("raw_state") or {}),
                            ),
                        )
        self._dirty = False

    def _soft_delete_absent_instances(self):
        """按当前内存实例集合收敛 PG 实例表。仅用于明确的删除/重铸造操作。"""
        if not self._current:
            return
        pid = self._current["id"]
        present_ids = list((self._current.get("instances") or {}).keys())
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                if present_ids:
                    cur.execute(
                        """UPDATE instance SET deleted_at = now()
                           WHERE project_id = %s AND deleted_at IS NULL
                             AND id <> ALL(%s)""",
                        (pid, present_ids),
                    )
                else:
                    cur.execute(
                        "UPDATE instance SET deleted_at = now() WHERE project_id = %s AND deleted_at IS NULL",
                        (pid,),
                    )

    def remove(self, instance_id):
        inst = super().remove(instance_id)
        if inst is not None and self._current:
            with pg.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE instance SET deleted_at = now() WHERE project_id = %s AND id = %s",
                        (self._current["id"], instance_id),
                    )
        return inst

    def clear_instances(self):
        with self._lock:
            if self._current:
                self._current["instances"] = {}
                self._save_current()
                self._soft_delete_absent_instances()

    def mint_instances(self):
        n = super().mint_instances()
        return n

    # ── 项目列举 / 数据集 ────────────────────────────────────
    def list_projects(self):
        out = []
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT p.id, p.name, p.created_at, p.dataset,
                              (SELECT count(*) FROM object_type o
                                 WHERE o.project_id = p.id AND o.deleted_at IS NULL),
                              (SELECT count(*) FROM instance i
                                 WHERE i.project_id = p.id AND i.deleted_at IS NULL),
                              (SELECT count(DISTINCT i.zone_id) FROM instance i
                                 WHERE i.project_id = p.id AND i.deleted_at IS NULL AND i.zone_id IS NOT NULL),
                              (SELECT count(*) FROM instance i
                                 WHERE i.project_id = p.id AND i.deleted_at IS NULL AND i.zone_id IS NULL)
                       FROM project p WHERE p.deleted_at IS NULL""",
                )
                for pid, name, created, dataset, tc, ic, zc, unzoned in cur.fetchall():
                    ds = dataset or {}
                    out.append({
                        "id": pid, "name": name, "created_at": created,
                        "type_count": tc, "instance_count": ic,
                        "zone_count": zc or 0,
                        "unzoned_instance_count": unzoned or 0,
                        "bound_ue_project_id": ds.get("bound_ue_project_id", ""),
                        "bound_ue_project_name": ds.get("bound_ue_project_name", ""),
                        "active": pid == self._active_id,
                    })
        return out

    def all_datasets(self):
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT dataset FROM project WHERE deleted_at IS NULL AND dataset IS NOT NULL"
                )
                return [r[0] for r in cur.fetchall() if r[0]]

    # ── 新建 / 删除 ──────────────────────────────────────────
    def create_project(self, name, object_types=None, calibration=None,
                       project_id=None, dataset=None):
        with self._lock:
            pid = project_id or f"p_{int(time.time() * 1000)}"
            proj = {
                "id": pid,
                "name": name,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataset": dataset,
                "object_types": object_types or {},
                "instances": {},
                "components": {},
                "instance_roster": [],
                "calibration": calibration,
                "spatial_profile": _default_spatial_profile(),
                "frames": [],
            }
            self._current = proj
            self._active_id = pid
            self._save_current()
            self._save_active()
            return proj

    def delete_project(self, pid):
        with self._lock:
            with pg.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM project WHERE id = %s AND deleted_at IS NULL", (pid,)
                    )
                    existed = cur.fetchone() is not None
                    if existed:
                        cur.execute(
                            "UPDATE project SET deleted_at = now() WHERE id = %s", (pid,)
                        )
            if self._active_id == pid:
                self._active_id = None
                self._current = None
                self._save_active()
            return existed
