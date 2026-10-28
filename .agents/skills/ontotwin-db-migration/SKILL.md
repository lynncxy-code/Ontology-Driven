---
name: ontotwin-db-migration
description: OntoTwin PostgreSQL 迁移与回滚纪律：区分 schema DDL 迁移（db/schema.sql 幂等）与 4.8 项目数据迁移（组织/工厂归属 + 冻结守卫），覆盖迁移路由、备份清单、内容哈希、回滚与恢复。当改表结构、改 schema.sql、做项目迁移/冻结/备份/恢复时使用。
---

# OntoTwin 数据库迁移规范

> 改数据库前先分清两件完全不同的「迁移」，它们机制不同、风险不同，混在一起就会出事。

## 0. 先分清两种迁移

| | A. Schema DDL 迁移 | B. 4.8 项目数据迁移 |
| :--- | :--- | :--- |
| 改的是什么 | 表结构 / 列 / 索引（`db/schema.sql`） | 项目的组织/工厂归属（业务数据搬动） |
| 代码位置 | `db/schema.sql`、`db/pg.py` | `project_store_pg.py` 冻结守卫、`tenant_api.py` 迁移路由 |
| 状态管理 | `project.schema_version` + `CURRENT_SCHEMA_VERSION` | `migration_batch` / `migration_scope` |
| 回滚手段 | 幂等 ALTER（加列）+ 手工恢复 | `trash_item`/`trash_snapshot` 软删 + `backup_manifest` |

## 1. Schema DDL 迁移（现状）

- 〔事实〕`db/schema.sql` 是**幂等**的：全部 `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，可重复执行（`db/schema.sql` 头注释）。
- 〔事实〕两条应用路径：
  1. docker initdb：`/docker-entrypoint-initdb.d/schema.sql`，**仅空数据卷首次**执行一次（`Dockerfile.4.8-rc-db`、`docker-compose.yml`）。
  2. `pg.init_schema()`：本地直跑或补建时执行整份 `schema.sql`（`db/pg.py`）。
- 〔事实〕连接层 `db/pg.py`：短连接 + `autocommit=True`，无连接池、无 ORM；`DATABASE_URL` 环境变量。
- 〔事实〕每个 `project` 行带 `schema_version INTEGER`，写入时用 `CURRENT_SCHEMA_VERSION`（`project_store_pg.py` `_save_current`）。
- 〔事实〕**改表结构的正确姿势（现状）**：把幂等 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 追加进 `schema.sql`；新库自动有，存量库执行一次 `pg.init_schema()` 补上（幂等，可重复跑）。
- 〔事实〕`db/pg.py` 连接用法固定：`with pg.get_conn() as conn: with conn.cursor() as cur: cur.execute(...)`。

## 2. 4.8 项目数据迁移（现状）

- 〔事实〕三段式流程，全部在 `/api/v4.8/*`（`tenant_api.py`）：
  - `POST /api/v4.8/migrations/preflight` —— 预检：校验项目归属冲突、生成 `preflight_report_json`。
  - `POST /api/v4.8/migrations/<id>/confirm` —— 必须显式 `confirm=true`；先冻结（`frozen`）再执行。
  - `GET /api/v4.8/migrations/<id>` / `GET .../legacy-bindings` —— 读批次与旧绑定核对。
  - `POST /api/v4.8/backups/manifest` —— 迁移前登记备份（`backup_manifest`）。
- 〔事实〕**冻结守卫**：`migration_scope JOIN migration_batch`，`mb.status IN ('frozen','running','rolling_back')` 即抛 `ProjectMigrationFrozenError`（`project_store_pg.py` `_guard_project_mutation`）。
- 〔事实〕守卫在**写层统一拦截**：`_save_current()` 开事务后第一件事查冻结，所以所有旧版写路径（包括直接 SQL 的删除）在冻结窗口内都被拦，不会把旧内存快照写回库（`project_store_pg.py` `_save_current`）。
- 〔事实〕**内容哈希校验**：`migration_scope.old_hash / new_hash` + `_project_content_hash()`；预检后内容变化 → 409 强制重新预检（`tenant_api.py` 迁移路由）。
- 〔事实〕回滚走软删：`trash_item` / `trash_snapshot`（`snapshot_ref` + `checksum`），不是直接 DROP。

## 3. 现状缺口（诚实标注，不是规范）

- 〔事实〕**没有版本化迁移 runner**：schema 变更只能靠「幂等 SQL 全量重跑」，无法按版本号追溯「哪个迁移已应用、哪个未应用」。
- 〔事实〕`schema.sql` initdb-only：存量库不会自动升级，依赖人工 `pg.init_schema()`（幂等 ALTER 是兜底，不是正式迁移）。
- 〔事实〕验收文档明确 block 的点：缺少「数据库备份 + 恢复演练」证据；`backup_manifest` 有登记雏形，但恢复流程未演练。

## 4. 业界成熟实践（补强，引入前与用户对齐）

- **版本化迁移**：编号迁移脚本（`0001_*.sql`、`0002_*.sql`）+ `schema_migrations` 表记录已应用版本，替代「全量幂等 SQL」。可追溯、可回滚、可增量。
- **迁移三段式**：备份 → 迁移 → 校验（`backup_manifest` 已有雏形，补「恢复演练」和「迁移后逐表校验」即可）。
- **原子性**：每个迁移单事务、失败整体回滚；不在迁移里混业务写。
- **向后兼容优先**：加列先 `nullable` + `DEFAULT`，读旧数据不破；删列先让代码停止读该列一轮，再删。
- **破坏性 DDL 必须有回滚预案**：`DROP` / `TRUNCATE` / `SET NOT NULL` 前先备份 + 演练。
- 迁移与业务写隔离（数据迁移的冻结守卫已做到；schema DDL 同样应选低峰/维护窗口）。

## 5. 禁止清单

- 迁移脚本里出现不带 `WHERE` 的 `UPDATE` / `DELETE`。
- 迁移脚本里混入业务逻辑或环境凭据/绝对路径。
- 跳过备份直接迁移。
- 破坏性 DDL（drop/truncate）没有回滚预案就执行。
- 把「项目数据迁移」（冻结/归属）和「schema DDL 迁移」当成一件事。

## 6. 自检

- 〔事实〕schema 改动：`schema.sql` 仍幂等可重跑；新库 initdb 与存量库 `pg.init_schema()` 都能出相同结构。
- 〔补强〕迁移在一次性副本上跑通：旧数据仍可读、回滚可执行、迁移前后项目内容哈希一致（数据迁移）。
- 〔补强〕记录「应用了哪个提交、哪个迁移、哪个备份、哪个环境」四要素。
