"""
PostgreSQL 连接层（OntoTwin 3.4）
============================================================
单人项目、低并发：不引入连接池依赖，按需开短连接（autocommit）。
连接串来自环境变量 DATABASE_URL；本地直跑（不走 docker）时用默认 localhost。

用法：
    from db import pg
    with pg.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ...")

启动时可调 pg.init_schema() 确保表存在（docker initdb 已首次自动建表，
本地直跑或已有空库时靠这个补建；schema.sql 全 IF NOT EXISTS，幂等）。
"""

import os
import psycopg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ontotwin:ontotwin@localhost:5432/ontotwin",
)

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_conn():
    """打开一个自动提交的连接（调用方用 with 管理生命周期）。"""
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_schema(schema_path=None):
    """执行 schema.sql 建表（幂等）。docker 首次已自动建；此处为本地/补建兜底。"""
    path = schema_path or _SCHEMA_PATH
    with open(path, "r", encoding="utf-8") as f:
        ddl = f.read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)


def ping():
    """连通性自检：返回 True 表示 PG 可连。"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
    except Exception:
        return False
