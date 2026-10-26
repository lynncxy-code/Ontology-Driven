-- ============================================================================
-- OntoTwin 3.4 —— PostgreSQL 真源 schema（本体 / 实例 / 分区）
--
-- 设计要点（见 PRD 3.4）：
--   * 单一真源；本体(项目级 object_types)/实例/分区 分表；嵌套块用 JSONB。
--   * 旧版路由仍可兼容当前激活项目；4.8 新路由按组织／工厂／项目会话核验。
--   * 全面软删：instance / zone / project 用 deleted_at 标记，查询过滤 NULL。
--   * 系统级 INTERFACES / OBJECT_TYPES / mapping_rules 不入库（保持代码/git 配置）。
--
-- 幂等：全部 IF NOT EXISTS，可重复执行；docker initdb 首次自动跑本文件。
-- ============================================================================

-- ── 单例键值（仅旧版兼容／诊断；4.8 不用作授权）────────────────────────────
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
    schema_version   INTEGER NOT NULL DEFAULT 1,
    dataset          JSONB,                -- 前端语义图谱数据集（含 graph_data）
    calibration      JSONB,                -- 坐标标定
    spatial_profile  JSONB,                -- 3.1 空间剖面（floor_table 仅留 z_base_mm）
    components        JSONB DEFAULT '{}',  -- 3.0 坐标标定匿名构件
    instance_roster  JSONB DEFAULT '[]',  -- 3.0 身份证号目录
    frames           JSONB DEFAULT '[]',  -- 3.1 帧注册表
    scene_interactions JSONB NOT NULL DEFAULT '{}', -- 4.0/4.0.1 人物与路线配置；图片元数据仍在 frames
    media_policy     JSONB NOT NULL DEFAULT '{}', -- 3.7.x 视频来源白名单与 HTTP 例外
    web_interactions JSONB NOT NULL DEFAULT '{}', -- 3.8 Web 页面、业务视图与绑定
    deleted_at       TIMESTAMPTZ
);

ALTER TABLE project ADD COLUMN IF NOT EXISTS schema_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE project ADD COLUMN IF NOT EXISTS scene_interactions JSONB NOT NULL DEFAULT '{}';
ALTER TABLE project ADD COLUMN IF NOT EXISTS media_policy JSONB NOT NULL DEFAULT '{}';
ALTER TABLE project ADD COLUMN IF NOT EXISTS web_interactions JSONB NOT NULL DEFAULT '{}';

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
    parent_zone_id TEXT,                   -- 3.8 父 Zone；空表示项目根级
    level       TEXT NOT NULL DEFAULT 'custom', -- building/floor/room/area/custom
    deleted_at  TIMESTAMPTZ,
    PRIMARY KEY (project_id, zone_id)
);

ALTER TABLE zone ADD COLUMN IF NOT EXISTS parent_zone_id TEXT;
ALTER TABLE zone ADD COLUMN IF NOT EXISTS level TEXT NOT NULL DEFAULT 'custom';

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
    display_name      TEXT,
    hierarchy_path    JSONB DEFAULT '[]',
    source_folder_path TEXT,
    source_asset_path TEXT,
    classification_status TEXT DEFAULT 'confirmed',
    classification_key TEXT,
    status            TEXT DEFAULT 'online',
    created_at        DOUBLE PRECISION,
    last_seen         DOUBLE PRECISION,
    render_config     JSONB DEFAULT '{}',
    raw_state         JSONB NOT NULL DEFAULT '{}',
    deleted_at        TIMESTAMPTZ,
    PRIMARY KEY (project_id, id)
);

ALTER TABLE instance ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE instance ADD COLUMN IF NOT EXISTS hierarchy_path JSONB DEFAULT '[]';
ALTER TABLE instance ADD COLUMN IF NOT EXISTS source_folder_path TEXT;
ALTER TABLE instance ADD COLUMN IF NOT EXISTS source_asset_path TEXT;
ALTER TABLE instance ADD COLUMN IF NOT EXISTS classification_status TEXT DEFAULT 'confirmed';
ALTER TABLE instance ADD COLUMN IF NOT EXISTS classification_key TEXT;

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

-- ============================================================================
-- OntoTwin 4.8 —— 组织、工厂、账号、项目上下文与场景级绑定
--
-- 4.8 不再把 app_singleton.active_project_id 当作授权或业务写入依据。
-- app_singleton 仅保留旧版本诊断兼容；新 API 使用 user_session 的上下文，
-- 每个浏览器会话独立保存 organization/factory/project。
-- 所有 ID 由应用生成并以 TEXT 保存，避免名称改动影响绑定和迁移幂等。
-- ============================================================================

CREATE TABLE IF NOT EXISTS environment (
    environment_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization (
    organization_id TEXT PRIMARY KEY,
    environment_id TEXT NOT NULL REFERENCES environment(environment_id),
    stable_group_id TEXT NOT NULL,
    name TEXT NOT NULL,
    logo_ref TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (environment_id, stable_group_id)
);

CREATE TABLE IF NOT EXISTS factory (
    factory_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organization(organization_id),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, name)
);

CREATE TABLE IF NOT EXISTS user_account (
    user_id TEXT PRIMARY KEY,
    environment_id TEXT NOT NULL REFERENCES environment(environment_id),
    login_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    password_revision INTEGER NOT NULL DEFAULT 1,
    failed_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    UNIQUE (environment_id, login_name)
);

CREATE TABLE IF NOT EXISTS user_session (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    session_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    invalidated_at TIMESTAMPTZ,
    password_revision INTEGER NOT NULL,
    current_organization_id TEXT REFERENCES organization(organization_id),
    current_factory_id TEXT REFERENCES factory(factory_id),
    current_project_id TEXT REFERENCES project(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization_member (
    organization_id TEXT NOT NULL REFERENCES organization(organization_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    status TEXT NOT NULL DEFAULT 'active',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMPTZ,
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS factory_member (
    factory_id TEXT NOT NULL REFERENCES factory(factory_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'active',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMPTZ,
    PRIMARY KEY (factory_id, user_id)
);

ALTER TABLE project ADD COLUMN IF NOT EXISTS environment_id TEXT;
ALTER TABLE project ADD COLUMN IF NOT EXISTS organization_id TEXT;
ALTER TABLE project ADD COLUMN IF NOT EXISTS factory_id TEXT;
ALTER TABLE project ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE project ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'project_environment_fk') THEN
        ALTER TABLE project ADD CONSTRAINT project_environment_fk
            FOREIGN KEY (environment_id) REFERENCES environment(environment_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'project_organization_fk') THEN
        ALTER TABLE project ADD CONSTRAINT project_organization_fk
            FOREIGN KEY (organization_id) REFERENCES organization(organization_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'project_factory_fk') THEN
        ALTER TABLE project ADD CONSTRAINT project_factory_fk
            FOREIGN KEY (factory_id) REFERENCES factory(factory_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_project_org_factory
    ON project (organization_id, factory_id) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS project_permission (
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    permission TEXT NOT NULL CHECK (permission IN ('view', 'edit')),
    granted_by TEXT REFERENCES user_account(user_id),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ,
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS audit_event (
    event_id TEXT PRIMARY KEY,
    actor_user_id TEXT REFERENCES user_account(user_id),
    organization_id TEXT REFERENCES organization(organization_id),
    factory_id TEXT REFERENCES factory(factory_id),
    project_id TEXT REFERENCES project(id),
    action TEXT NOT NULL,
    target TEXT,
    result TEXT NOT NULL,
    detail JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ue_project (
    ue_project_id TEXT PRIMARY KEY,
    stable_key TEXT NOT NULL UNIQUE,
    display_name TEXT,
    last_seen_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ue_scene (
    scene_id TEXT PRIMARY KEY,
    ue_project_id TEXT NOT NULL REFERENCES ue_project(ue_project_id) ON DELETE CASCADE,
    stable_key TEXT NOT NULL,
    display_name TEXT,
    level_path TEXT,
    UNIQUE (ue_project_id, stable_key)
);

CREATE TABLE IF NOT EXISTS project_scene_binding (
    binding_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    organization_id TEXT NOT NULL REFERENCES organization(organization_id),
    factory_id TEXT NOT NULL REFERENCES factory(factory_id),
    ue_project_id TEXT NOT NULL REFERENCES ue_project(ue_project_id),
    scene_id TEXT NOT NULL REFERENCES ue_scene(scene_id),
    status TEXT NOT NULL DEFAULT 'active',
    bound_by TEXT REFERENCES user_account(user_id),
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_scene_binding_project
    ON project_scene_binding(project_id) WHERE status = 'active';
CREATE UNIQUE INDEX IF NOT EXISTS uq_project_scene_binding_scene
    ON project_scene_binding(ue_project_id, scene_id) WHERE status = 'active';

CREATE TABLE IF NOT EXISTS ue_connection (
    connection_id TEXT PRIMARY KEY,
    ue_project_id TEXT NOT NULL REFERENCES ue_project(ue_project_id),
    scene_id TEXT NOT NULL REFERENCES ue_scene(scene_id),
    project_id TEXT REFERENCES project(id),
    session_id TEXT REFERENCES user_session(session_id),
    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'connected'
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ue_connection_live
    ON ue_connection(ue_project_id, scene_id) WHERE released_at IS NULL AND status = 'connected';

CREATE TABLE IF NOT EXISTS legacy_binding_review (
    review_id TEXT PRIMARY KEY,
    legacy_project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    legacy_ue_project_id TEXT,
    candidate_scene_id TEXT REFERENCES ue_scene(scene_id),
    status TEXT NOT NULL DEFAULT 'pending',
    evidence_json JSONB NOT NULL DEFAULT '{}',
    decision_note TEXT,
    reviewed_by TEXT REFERENCES user_account(user_id),
    reviewed_at TIMESTAMPTZ,
    UNIQUE (legacy_project_id, legacy_ue_project_id)
);

CREATE TABLE IF NOT EXISTS migration_batch (
    migration_id TEXT PRIMARY KEY,
    environment_id TEXT NOT NULL REFERENCES environment(environment_id),
    status TEXT NOT NULL DEFAULT 'preflight',
    freeze_started_at TIMESTAMPTZ,
    backup_id TEXT,
    preflight_report_json JSONB NOT NULL DEFAULT '{}',
    confirmed_by TEXT REFERENCES user_account(user_id),
    confirmed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failure_code TEXT,
    rollback_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS migration_scope (
    migration_id TEXT NOT NULL REFERENCES migration_batch(migration_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    old_hash TEXT,
    new_hash TEXT,
    PRIMARY KEY (migration_id, project_id)
);

CREATE TABLE IF NOT EXISTS project_config_migration (
    migration_id TEXT NOT NULL REFERENCES migration_batch(migration_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    source_revision TEXT,
    source_state JSONB NOT NULL DEFAULT '{}',
    target_state JSONB NOT NULL DEFAULT '{}',
    auto_apply BOOLEAN NOT NULL DEFAULT FALSE,
    review_status TEXT NOT NULL DEFAULT 'isolated',
    PRIMARY KEY (migration_id, project_id, module)
);

CREATE TABLE IF NOT EXISTS trash_item (
    trash_id TEXT PRIMARY KEY,
    organization_id TEXT REFERENCES organization(organization_id),
    factory_id TEXT REFERENCES factory(factory_id),
    project_id TEXT REFERENCES project(id),
    kind TEXT NOT NULL,
    snapshot_ref TEXT,
    deleted_by TEXT REFERENCES user_account(user_id),
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    purge_after TIMESTAMPTZ,
    migration_id TEXT REFERENCES migration_batch(migration_id),
    visibility_status TEXT NOT NULL DEFAULT 'visible'
);

CREATE TABLE IF NOT EXISTS trash_snapshot (
    snapshot_ref TEXT PRIMARY KEY,
    payload_ref TEXT NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_manifest (
    backup_id TEXT PRIMARY KEY,
    environment_id TEXT NOT NULL REFERENCES environment(environment_id),
    storage_uri TEXT NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    restored_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_session_active ON user_session(user_id, expires_at)
    WHERE invalidated_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_factory_member_user ON factory_member(user_id)
    WHERE removed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_org_member_user ON organization_member(user_id)
    WHERE removed_at IS NULL;
