"""
一次性导入：data/projects/*.json + data/active.json  →  PostgreSQL（OntoTwin 3.4）
============================================================
把现有 JSON 版 ProjectStore 的数据灌进 PG（FR-1 初始化路径）。
复用 ProjectStorePG._save_current 的拆表逻辑，保证与运行时写入完全一致。

幂等：可重复跑（项目/本体整表替换、实例 upsert）。不会动 JSON 原文件。

运行（需 PG 可连，即 docker 的 db 服务已起）：
    # 容器内
    docker compose exec backend python -m tools.import_json_to_pg
    # 或本地（需本地 psycopg + 可连 PG，设好 DATABASE_URL）
    cd backend && python -m tools.import_json_to_pg
"""

import os
import json
import glob

from project_store_pg import ProjectStorePG
from db import pg

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_PROJECTS_DIR = os.path.join(_DATA_DIR, "projects")
_ACTIVE_FILE = os.path.join(_DATA_DIR, "active.json")


def _ensure_shape(proj):
    """补齐可能缺失的集合键，避免 _save_current 取值出错（与 JSON 版一致）。"""
    proj.setdefault("object_types", {})
    proj.setdefault("instances", {})
    proj.setdefault("components", {})
    proj.setdefault("instance_roster", [])
    proj.setdefault("frames", [])
    proj.setdefault("dataset", None)
    proj.setdefault("calibration", None)
    proj.setdefault("spatial_profile", None)
    return proj


def main():
    if not pg.ping():
        raise SystemExit("PG 连不上，请先起 db 服务（docker compose up -d db）并检查 DATABASE_URL")

    pg.init_schema()
    store = ProjectStorePG()

    files = sorted(glob.glob(os.path.join(_PROJECTS_DIR, "*.json")))
    if not files:
        print(f"未发现待导入项目：{_PROJECTS_DIR}")
        return

    imported = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                proj = _ensure_shape(json.load(f))
        except Exception as e:
            print(f"跳过（读取失败）{os.path.basename(path)}: {e}")
            continue
        pid = proj.get("id")
        if not pid:
            print(f"跳过（无 id）{os.path.basename(path)}")
            continue
        # 借用内存模型 + 拆表落盘逻辑
        store._current = proj
        store._active_id = pid
        store._save_current()
        imported += 1
        print(f"已导入 {pid}  类型 {len(proj['object_types'])} | 实例 {len(proj['instances'])}")

    # 恢复原激活项目
    active_id = None
    if os.path.exists(_ACTIVE_FILE):
        try:
            with open(_ACTIVE_FILE, "r", encoding="utf-8") as f:
                active_id = json.load(f).get("active_project_id")
        except Exception:
            active_id = None
    store._active_id = active_id
    store._current = store._read_project(active_id) if active_id else None
    store._save_active()

    print(f"\n完成：导入 {imported} 个项目；激活项目 = {active_id or '(无)'}")


if __name__ == "__main__":
    main()
