#!/usr/bin/env python3
"""Consolidate model-specific ZHHZ ObjectTypes into business-shape types.

The migration is deliberately project-scoped and transactional.  It changes
only ObjectType records and instance type references; instance IDs, transforms,
render_config, raw_state, and lifecycle/deletion state remain untouched.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os

import psycopg
from psycopg.types.json import Jsonb


PROJECT_ID = "ds_1784694647848"
PROJECT_NAME = "ZHHZ"
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ontotwin:ontotwin@db:5432/ontotwin"
)


TARGETS = (
    {
        "rid": "zhhz.furniture.modular_sofa",
        "name": "浅灰模块沙发",
        "sources": (
            "zhhz.furniture.model_00f6e344f4bc728d",
            "zhhz.furniture.model_1e271d28426dbb11",
            "zhhz.furniture.model_61c27ee7c2b1fe3f",
            "zhhz.furniture.model_c5aac92959d48644",
        ),
    },
    {
        "rid": "zhhz.furniture.black_edge_console",
        "name": "黑边操作台",
        "sources": (
            "zhhz.furniture.model_08b8830e0759ec98",
            "zhhz.furniture.model_2c43c2099c60a0f1",
            "zhhz.furniture.model_76d7245c5c5eb6f3",
            "zhhz.furniture.model_8af3f2d41ac15d21",
            "zhhz.furniture.model_c1be81bd0e519f10",
        ),
    },
    {
        "rid": "zhhz.furniture.display_table",
        "name": "展示桌",
        "sources": ("zhhz.furniture.model_475c912888eccf1b",),
    },
    {
        "rid": "zhhz.exhibit_fixture.white_beveled_plinth",
        "name": "白色倒角展台",
        "sources": (
            "zhhz.exhibit_fixture.model_054920a28ec53d60",
            "zhhz.exhibit_fixture.model_516560622e254031",
            "zhhz.exhibit_fixture.model_c728139672c62f2e",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.monochrome_combination_plinth",
        "name": "黑白/灰黑组合展台",
        "sources": (
            "zhhz.exhibit_fixture.model_0b4ccec734c275fb",
            "zhhz.exhibit_fixture.model_3b5a403c5180d3d0",
            "zhhz.exhibit_fixture.model_59b82b91f1cd460e",
            "zhhz.exhibit_fixture.model_9a4f0499c9482fdf",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.light_neutral_combination_plinth",
        "name": "白灰组合展台",
        "sources": (
            "zhhz.exhibit_fixture.model_0c479112746dcc7e",
            "zhhz.exhibit_fixture.model_628abc0c7e6e42b9",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.large_composite_fixture",
        "name": "大型复合展陈装置",
        "sources": (
            "zhhz.exhibit_fixture.model_11faae0c2e1ae337",
            "zhhz.exhibit_fixture.model_41d52d8fe3054627",
            "zhhz.exhibit_fixture.model_4c6958ddf91d4a68",
            "zhhz.exhibit_fixture.model_52b4ef67231b1f24",
            "zhhz.exhibit_fixture.model_546b466c8fa0689f",
            "zhhz.exhibit_fixture.model_726121c8e520f34f",
            "zhhz.exhibit_fixture.model_8ed7fb5b004bd585",
            "zhhz.exhibit_fixture.model_ad28cfe223b46602",
            "zhhz.exhibit_fixture.model_b21555c5a7d704ae",
            "zhhz.exhibit_fixture.model_b5ef33db2120c9bf",
            "zhhz.exhibit_fixture.model_d907bfd5c5272a6a",
            "zhhz.exhibit_fixture.model_fc28a7d285b69bba",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.graphic_display_plinth",
        "name": "图文组合展台",
        "sources": ("zhhz.exhibit_fixture.model_1738f547ab972655",),
    },
    {
        "rid": "zhhz.exhibit_fixture.star_luminous_plinth",
        "name": "星形发光展台",
        "sources": (
            "zhhz.exhibit_fixture.model_4e207aa4d2609660",
            "zhhz.exhibit_fixture.model_59c9f5a990a7b7bb",
            "zhhz.exhibit_fixture.model_cf1793fb61cb3c4e",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.small_white_plinth",
        "name": "小型白色展台",
        "sources": ("zhhz.exhibit_fixture.model_5d26575f9efc156d",),
    },
    {
        "rid": "zhhz.exhibit_fixture.blue_white_plinth",
        "name": "蓝白组合展台",
        "sources": ("zhhz.exhibit_fixture.model_68df85f64af653f3",),
    },
    {
        "rid": "zhhz.exhibit_fixture.luminous_information_sign",
        "name": "发光信息牌",
        "sources": ("zhhz.exhibit_fixture.model_6f12aaee9e552936",),
    },
    {
        "rid": "zhhz.exhibit_fixture.eight_component_white_plinth",
        "name": "八组件白色展台",
        "sources": (
            "zhhz.exhibit_fixture.model_838ad322811e2f63",
            "zhhz.exhibit_fixture.model_d4d40631a397d955",
        ),
    },
    {
        "rid": "zhhz.exhibit_fixture.general_aviation_fixture",
        "name": "通航综合展陈装置",
        "sources": ("zhhz.exhibit_fixture.model_598eb999fc37ba56",),
    },
    {
        "rid": "zhhz.exhibit_fixture.graphic_panel",
        "name": "图文展板",
        "sources": ("zhhz.exhibit_fixture.model_c2a2d47995ebc347",),
    },
    {
        "rid": "zhhz.display_media_device.led_screen",
        "name": "LED显示屏",
        "sources": (
            "zhhz.display_media_device.model_007904e7e325c5ae",
            "zhhz.display_media_device.model_00c7287cd8769399",
            "zhhz.display_media_device.model_3ab88f8bc986d303",
            "zhhz.display_media_device.model_4e7bb02b7b4f1e87",
            "zhhz.display_media_device.model_56714c240da8f421",
            "zhhz.display_media_device.model_620acb0b59b3c48a",
            "zhhz.display_media_device.model_6ec7712d009c4ccf",
            "zhhz.display_media_device.model_8a8df6309530810f",
            "zhhz.display_media_device.model_8cf8dc7346e2a138",
            "zhhz.display_media_device.model_dba0a37cd0a239f9",
            "zhhz.display_media_device.model_ef3dfa4e2519dec9",
            "zhhz.display_media_device.model_f40e11059cd3c75e",
        ),
    },
    {
        "rid": "zhhz.display_media_device.composite_media_display",
        "name": "组合媒体展示屏",
        "sources": (
            "zhhz.display_media_device.model_291322bd2b0460c3",
            "zhhz.display_media_device.model_f517c63c5bc5163b",
        ),
    },
    {
        "rid": "zhhz.display_media_device.standalone_media_display",
        "name": "独立媒体展示屏",
        "sources": ("zhhz.display_media_device.model_2ee1fc469690eb4b",),
    },
    {
        "rid": "zhhz.aircraft_model_equipment.fixed_wing_model",
        "name": "固定翼飞机航模",
        "sources": (
            "zhhz.aircraft_model_equipment.model_a10fe57216ee6b50",
            "zhhz.aircraft_model_equipment.model_bc7ed32903d9b1f1",
            "zhhz.aircraft_model_equipment.model_cfa6746a624f1f89",
            "zhhz.aircraft_model_equipment.model_8f75148c44f1e6bd",
            "zhhz.aircraft_model_equipment.model_d009e8fb6095b5ee",
            "zhhz.aircraft_model_equipment.model_d41400282c3b2ce0",
        ),
    },
    {
        "rid": "zhhz.aircraft_model_equipment.rotorcraft_model",
        "name": "旋翼飞机航模",
        "sources": ("zhhz.aircraft_model_equipment.model_58d4fa1ee88e2802",),
    },
    {
        "rid": "zhhz.aircraft_model_equipment.propulsion_model",
        "name": "航空动力装置模型",
        "sources": (
            "zhhz.aircraft_model_equipment.model_41ea398b3086fcb0",
            "zhhz.aircraft_model_equipment.model_79bde7f7c5f76d43",
            "zhhz.aircraft_model_equipment.model_734cc84dc7f4b0b3",
            "zhhz.aircraft_model_equipment.model_88edfba25fa5ebbb",
            "zhhz.aircraft_model_equipment.model_d504e208f13289f6",
            "zhhz.aircraft_model_equipment.model_ffe19151fd044282",
            "zhhz.aircraft_model_equipment.model_7e2c7360ce4b000b",
        ),
    },
    {
        "rid": "zhhz.aircraft_model_equipment.cockpit_model",
        "name": "座舱模型",
        "sources": ("zhhz.aircraft_model_equipment.model_e4d1d0303f98750d",),
    },
)


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def fingerprint_other_projects(conn) -> str:
    payload = {}
    with conn.cursor() as cur:
        for table, where_column in (
            ("project", "id"),
            ("object_type", "project_id"),
            ("zone", "project_id"),
            ("instance", "project_id"),
        ):
            cur.execute(f"SELECT * FROM {table} WHERE {where_column} <> %s ORDER BY 1, 2", (PROJECT_ID,))
            columns = [item.name for item in cur.description]
            payload[table] = [dict(zip(columns, values)) for values in cur.fetchall()]
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def target_record(spec, source_records):
    interfaces = []
    for record in source_records:
        for interface in record.get("injected_interfaces") or []:
            if interface not in interfaces:
                interfaces.append(interface)
    return {
        "rid": spec["rid"],
        "name": spec["name"],
        "category": "UE Migration",
        "description": "按业务形态由既有 ZHHZ UE 迁移类型归并；具体模型装配保留在实例配置中。",
        "color": source_records[0].get("color") or "#8a8a8a",
        "properties": [],
        "injected_interfaces": interfaces or ["I3D_Representable", "I3D_Spatial"],
        "interface_configs": {},
        "asset_id": None,
        "ue_asset_path": "",
        "mock_instances": [],
        "source": "ue_migration_consolidation",
        "lifecycle_status": "EXPERIMENTAL",
        "consolidated_from": list(spec["sources"]),
    }


def inspect(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM project WHERE id = %s", (PROJECT_ID,))
        project = cur.fetchone()
        if not project or project[0] != PROJECT_NAME:
            raise RuntimeError(f"Expected active ZHHZ project row, got {project!r}")
        cur.execute(
            "SELECT rid, name, data FROM object_type WHERE project_id = %s AND deleted_at IS NULL",
            (PROJECT_ID,),
        )
        type_rows = {rid: {"name": name, "data": data or {}} for rid, name, data in cur.fetchall()}
        cur.execute(
            "SELECT object_type_rid, count(*) FROM instance "
            "WHERE project_id = %s AND deleted_at IS NULL GROUP BY object_type_rid",
            (PROJECT_ID,),
        )
        live_counts = dict(cur.fetchall())
        cur.execute(
            "SELECT count(*) FROM instance WHERE project_id = %s AND deleted_at IS NULL",
            (PROJECT_ID,),
        )
        live_instances = cur.fetchone()[0]

    source_to_target = {}
    for spec in TARGETS:
        if spec["rid"] in type_rows:
            raise RuntimeError(f"Target RID already exists: {spec['rid']}")
        for source in spec["sources"]:
            if source in source_to_target:
                raise RuntimeError(f"Source RID mapped more than once: {source}")
            if source not in type_rows:
                raise RuntimeError(f"Missing source RID: {source}")
            source_to_target[source] = spec["rid"]

    source_count = len(source_to_target)
    affected_instances = sum(live_counts.get(source, 0) for source in source_to_target)
    summary = {
        "project_id": PROJECT_ID,
        "before_type_count": len(type_rows),
        "before_live_instance_count": live_instances,
        "source_type_count": source_count,
        "target_type_count": len(TARGETS),
        "expected_after_type_count": len(type_rows) - source_count + len(TARGETS),
        "affected_live_instances": affected_instances,
    }
    if summary != {
        "project_id": PROJECT_ID,
        "before_type_count": 82,
        "before_live_instance_count": 229,
        "source_type_count": 72,
        "target_type_count": 22,
        "expected_after_type_count": 32,
        "affected_live_instances": 87,
    }:
        raise RuntimeError("Preflight metrics differ from approved plan: " + canonical(summary))
    return type_rows, source_to_target, summary


def apply(conn, type_rows, source_to_target, summary):
    other_before = fingerprint_other_projects(conn)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (1784694647848,))
            for spec in TARGETS:
                sources = [copy.deepcopy(type_rows[rid]["data"]) for rid in spec["sources"]]
                record = target_record(spec, sources)
                cur.execute(
                    "INSERT INTO object_type (project_id, rid, name, source, data, deleted_at) "
                    "VALUES (%s, %s, %s, %s, %s, NULL)",
                    (
                        PROJECT_ID,
                        spec["rid"],
                        spec["name"],
                        record["source"],
                        Jsonb(record),
                    ),
                )
                cur.execute(
                    "UPDATE instance SET object_type_rid = %s, object_type_name = %s "
                    "WHERE project_id = %s AND object_type_rid = ANY(%s)",
                    (spec["rid"], spec["name"], PROJECT_ID, list(spec["sources"])),
                )

            cur.execute(
                "DELETE FROM object_type WHERE project_id = %s AND rid = ANY(%s)",
                (PROJECT_ID, list(source_to_target)),
            )

            cur.execute(
                "SELECT count(*) FROM object_type WHERE project_id = %s AND deleted_at IS NULL",
                (PROJECT_ID,),
            )
            if cur.fetchone()[0] != summary["expected_after_type_count"]:
                raise RuntimeError("Unexpected post-migration Type count")
            cur.execute(
                "SELECT count(*) FROM instance WHERE project_id = %s AND deleted_at IS NULL",
                (PROJECT_ID,),
            )
            if cur.fetchone()[0] != summary["before_live_instance_count"]:
                raise RuntimeError("Live instance count changed")
            cur.execute(
                "SELECT count(*) FROM instance i LEFT JOIN object_type t "
                "ON t.project_id = i.project_id AND t.rid = i.object_type_rid AND t.deleted_at IS NULL "
                "WHERE i.project_id = %s AND i.deleted_at IS NULL AND t.rid IS NULL",
                (PROJECT_ID,),
            )
            if cur.fetchone()[0] != 0:
                raise RuntimeError("A live instance references a missing Type")
            cur.execute(
                "SELECT count(*) FROM instance WHERE project_id = %s AND deleted_at IS NULL "
                "AND object_type_rid = ANY(%s)",
                (PROJECT_ID, list(source_to_target)),
            )
            if cur.fetchone()[0] != 0:
                raise RuntimeError("A live instance still references a source Type")

        other_after = fingerprint_other_projects(conn)
        if other_after != other_before:
            raise RuntimeError("Other-project fingerprint changed")

    return {**summary, "other_projects_sha256": other_before, "status": "APPLIED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with psycopg.connect(DATABASE_URL) as conn:
        type_rows, source_to_target, summary = inspect(conn)
        if args.apply:
            result = apply(conn, type_rows, source_to_target, summary)
        else:
            result = {**summary, "status": "DRY_RUN_OK"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
