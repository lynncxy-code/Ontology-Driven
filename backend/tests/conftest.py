"""
pytest 测试脚手架（MCP M0 后端）
================================================================
提供隔离的临时 ProjectStore，绝不触碰真实 backend/data。

运行工作目录必须是 backend/（app.py 用无包顶层 import）：
    cd backend && python -m pytest -q

fixtures:
- tmp_data : 临时数据根目录，测试结束自动清理。
- store    : 已激活的隔离 ProjectStore，含 1 个类型（rid=PE16A）
             + 2 个已绑定构件（bound_instance_id = DW-001 / DW-002），
             可被 mint_instances() 铸造出 DW-001 / DW-002 两个实例。
- client   : Flask test client，app.project_store / app.instance_store
             已重定向到隔离 store（供后续 handler 测试用）。
"""

import os
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp_data():
    d = tempfile.mkdtemp(prefix="ots_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def store(tmp_data, monkeypatch):
    # 先把 project_store 的存储路径全局指向隔离目录，再构造 ProjectStore()。
    # ProjectStore.__init__ 以这些模块全局作为默认值，故 monkeypatch 后即隔离。
    import project_store as ps

    projects_dir = os.path.join(tmp_data, "projects")
    active_file = os.path.join(tmp_data, "active.json")
    monkeypatch.setattr(ps, "_DATA_DIR", tmp_data)
    monkeypatch.setattr(ps, "_PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(ps, "_ACTIVE_FILE", active_file)

    s = ps.ProjectStore()  # 读取上面 patch 过的全局默认值 → 落在 tmp_data
    s.create_project(
        "测试厂",
        object_types={"PE16A": {"rid": "PE16A", "name": "溶铜槽"}},
        project_id="p_test",
    )

    # 造 2 个已绑定构件；字段以 mint_instances() 实际消费的为准
    # （bound_instance_id / object_type_rid / type_name / ue_xy / render_config / id）。
    def _seed_components(w):
        comps = w.setdefault("components", {})
        comps.update({
            "c1": {
                "id": "c1",
                "object_type_rid": "PE16A",
                "type_name": "溶铜槽",
                "bound_instance_id": "DW-001",
                "ue_xy": [0, 0],
                "render_config": {},
            },
            "c2": {
                "id": "c2",
                "object_type_rid": "PE16A",
                "type_name": "溶铜槽",
                "bound_instance_id": "DW-002",
                "ue_xy": [1, 1],
                "render_config": {},
            },
        })

    s.transact_active(_seed_components)
    return s


@pytest.fixture
def client(store, monkeypatch):
    """Flask test client，指向同一隔离 store。

    依赖 store fixture：其 monkeypatch 已把 project_store 存储路径指向隔离目录，
    因此 app 在 import 时构造的 ProjectStore 也落在临时目录（不碰真实 data）。
    随后把 app 的模块级 project_store / instance_store 重定向到本 store，
    Flask handler 在运行时按模块全局名查找，故请求会走隔离 store。
    """
    import app as app_module

    monkeypatch.setattr(app_module, "project_store", store)
    monkeypatch.setattr(app_module, "instance_store", store)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
