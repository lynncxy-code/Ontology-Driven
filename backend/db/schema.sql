-- ============================================================================
-- OntoTwin 3.4 —— PostgreSQL 真源 schema（本体 / 实例 / 分区）
--
-- 设计要点（见 PRD 3.4）：
--   * 单一真源；本体(项目级 object_types)/实例/分区 分表；嵌套块用 JSONB。
--   * "唯一可见性规则" 由应用层保证（只读当前激活项目）；DB 存全部项目。
--   * 全面软删：instance / zone / project 用 deleted_at 标记，查询过滤 NULL。
--   * 系统级 INTERFACES / OBJECT_TYPES / mapping_rules 不入库（保持代码/git 配置）。
--
-- 幂等：全部 IF NOT EXISTS，可重复执行；docker initdb 首次自动跑本文件。
-- ============================================================================

-- ── 单例键值（记录当前激活项目等）─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS app_singleton (
    k TEXT PRIMARY KEY,
    v TEXT
);

-- ── 项目（一 Project = 一厂区/站点的全部自洽数据）────────────────────────
-- 会变但低频的项目级嵌套块直接放 JSONB（不参与查询）。
CREATE TABLE IF NOT EXISTS project (
    id               TEXT PRIMARY KEY,
    name             TEXT,
    created_at       TEXT,                 -- 沿用原格式 'YYYY-MM-DD HH:MM:SS'
    dataset          JSONB,                -- 前端语义图谱数据集（含 graph_data）
    calibration      JSONB,                -- 坐标标定
    spatial_profile  JSONB,                -- 3.1 空间剖面（floor_table 仅留 z_base_mm）
    components        JSONB DEFAULT '{}',  -- 3.0 坐标标定匿名构件
    instance_roster  JSONB DEFAULT '[]',  -- 3.0 身份证号目录
    frames           JSONB DEFAULT '[]',  -- 3.1 帧注册表
    deleted_at       TIMESTAMPTZ
);

-- ── 本体（项目级类型注册表）────────────────────────────────────────────────
-- data 存完整类型记录；rid/name/source 提列便于查询与迁移归类。
CREATE TABLE IF NOT EXISTS object_type (
    project_id  TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    rid         TEXT NOT NULL,
    name        TEXT,
    source      TEXT,                      -- 例：'cad_auto:五楼.dxf' / 'legacy' / 'ontotwin'
    data        JSONB NOT NULL DEFAULT '{}',
    deleted_at  TIMESTAMPTZ,
    PRIMARY KEY (project_id, rid)
);

-- ── 分区登记表（zone → UE 关卡地图 + 流送信息）────────────────────────────
CREATE TABLE IF NOT EXISTS zone (
    project_id  TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    zone_id     TEXT NOT NULL,
    name        TEXT,
    ue_level    TEXT,                      -- UE 子关卡/地图路径
    streaming   JSONB DEFAULT '{}',        -- 流送信息（预留：加载策略等）
    deleted_at  TIMESTAMPTZ,
    PRIMARY KEY (project_id, zone_id)
);

-- ── 实例（高频变；raw_state/render_config 用 JSONB）────────────────────────
CREATE TABLE IF NOT EXISTS instance (
    project_id        TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    id                TEXT NOT NULL,
    object_type_rid   TEXT,
    object_type_name  TEXT,
    zone_id           TEXT,                -- 分区路由键（可空；MVP 单关卡可为 NULL）
    component_id      TEXT,                -- 绑定的 CAD 构件（自由实例为 NULL）
    source            TEXT DEFAULT 'ontotwin',  -- 'ontotwin' | 'ue_migrated'
    ext_guid          TEXT,                -- UE ActorGuid（迁移收编用，幂等键）
    status            TEXT DEFAULT 'online',
    created_at        DOUBLE PRECISION,
    last_seen         DOUBLE PRECISION,
    render_config     JSONB DEFAULT '{}',
    raw_state         JSONB NOT NULL DEFAULT '{}',
    deleted_at        TIMESTAMPTZ,
    PRIMARY KEY (project_id, id)
);

-- ── 索引 ──────────────────────────────────────────────────────────────────
-- 按分区过滤（FR-3 snapshots 加 zone 过滤）；仅索引未删行。
CREATE INDEX IF NOT EXISTS idx_instance_zone
    ON instance (project_id, zone_id) WHERE deleted_at IS NULL;
-- 迁移幂等：按 ActorGuid 查重。
CREATE INDEX IF NOT EXISTS idx_instance_ext_guid
    ON instance (project_id, ext_guid) WHERE ext_guid IS NOT NULL;
-- 活实例遍历。
CREATE INDEX IF NOT EXISTS idx_instance_live
    ON instance (project_id) WHERE deleted_at IS NULL;
