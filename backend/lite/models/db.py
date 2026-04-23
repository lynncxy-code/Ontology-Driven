"""SQLite 连接管理与表初始化。

数据库文件位置：backend/lite/db/lite.db
所有表以 lite_ 为前缀，与现有 Nexus 存储完全隔离（ADR-012）。
"""
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent.parent / "db" / "lite.db"


def get_connection() -> sqlite3.Connection:
    """返回一个 sqlite3 连接，Row 模式（可按列名访问）。"""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """首次启动时建表（已存在则跳过）。"""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    with conn:
        conn.executescript(_SCHEMA_SQL)
    conn.close()
    print(f"[Lite DB] 初始化完成: {_DB_PATH}")


_SCHEMA_SQL = """
-- 资产库：FBX 源文件 + USD 缓存路径
CREATE TABLE IF NOT EXISTS lite_assets (
    file_number       TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    fbx_source_path   TEXT NOT NULL,
    usd_cached_path   TEXT,
    usd_cache_hash    TEXT,
    usd_cached_at     TIMESTAMP,
    bounding_box      TEXT,          -- JSON: {"x":0.8,"y":2.0,"z":2.0}
    mass_hint         REAL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 实例：场景里的每一个物体
CREATE TABLE IF NOT EXISTS lite_instances (
    id                TEXT PRIMARY KEY,
    object_type_rid   TEXT NOT NULL,
    file_number       TEXT NOT NULL,
    display_name      TEXT,
    translation_x     REAL DEFAULT 0,
    translation_y     REAL DEFAULT 0,
    translation_z     REAL DEFAULT 0,
    rotation_x        REAL DEFAULT 0,
    rotation_y        REAL DEFAULT 0,
    rotation_z        REAL DEFAULT 0,
    scale_x           REAL DEFAULT 1,
    scale_y           REAL DEFAULT 1,
    scale_z           REAL DEFAULT 1,
    collision_type    TEXT DEFAULT 'static',
    mass              REAL,
    friction          REAL DEFAULT 0.5,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_number) REFERENCES lite_assets(file_number)
);

-- 场景：一组实例的空间组织
CREATE TABLE IF NOT EXISTS lite_scenes (
    id                TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    description       TEXT,
    bounds_x_min      REAL NOT NULL,
    bounds_x_max      REAL NOT NULL,
    bounds_y_min      REAL NOT NULL,
    bounds_y_max      REAL NOT NULL,
    bounds_z_min      REAL NOT NULL,
    bounds_z_max      REAL NOT NULL,
    up_axis           TEXT DEFAULT 'Z',
    unit              TEXT DEFAULT 'meter',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 场景-实例多对多关联
CREATE TABLE IF NOT EXISTS lite_scene_instances (
    scene_id          TEXT NOT NULL,
    instance_id       TEXT NOT NULL,
    PRIMARY KEY (scene_id, instance_id),
    FOREIGN KEY (scene_id)    REFERENCES lite_scenes(id)    ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES lite_instances(id) ON DELETE CASCADE
);

-- 导出记录
CREATE TABLE IF NOT EXISTS lite_exports (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id          TEXT NOT NULL,
    version           INTEGER NOT NULL,
    file_path         TEXT NOT NULL,
    file_size_bytes   INTEGER,
    exported_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_json       TEXT,
    FOREIGN KEY (scene_id) REFERENCES lite_scenes(id)
);
"""
