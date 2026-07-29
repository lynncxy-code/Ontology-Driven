from ontotwin_mcp.errors import map_response_error, map_transport_error, NexusError
import httpx


def test_no_active_project_hint():
    e = map_response_error("save_components", 400, '{"error":"当前无激活项目，请先..."}', {"error": "当前无激活项目，请先..."})
    assert e.http_status == 400 and "activate_project" in str(e)


def test_generic_400_no_false_hint():
    e = map_response_error("upload_roster", 400, '{"error":"缺少必须的文件"}', {"error": "缺少必须的文件"})
    assert e.code == "NEXUS_VALIDATION_ERROR" and "activate_project" not in str(e)
    assert e.retryable is False


def test_409_project_changed():
    e = map_response_error("mint_instances", 409, '{"error":"project changed","expected":"a","actual":"b"}', {"error": "project changed", "expected": "a", "actual": "b"})
    assert e.http_status == 409 and "a" in str(e) and "b" in str(e)


def test_409_non_dict_parsed_json_no_crash():
    # parsed_json 是非 dict 的合法 JSON（如 list）时，409 分支不应 AttributeError，
    # 而应回退到空 dict 并返回合理的 NexusError。不含 expected/actual → NEXUS_CONFLICT。
    e = map_response_error("mint_instances", 409, '["a","b"]', ["a", "b"])
    assert isinstance(e, NexusError)
    assert e.http_status == 409 and e.code == "NEXUS_CONFLICT"


def test_409_name_duplicated_is_conflict_not_project_changed():
    # create_empty_project 重名也是 409，但不带 expected/actual，
    # 必须映射为 NEXUS_CONFLICT（透传 error），而非误导性的 NEXUS_PROJECT_CHANGED。
    e = map_response_error("create_empty_project", 409,
                           '{"error":"name_duplicated"}', {"error": "name_duplicated"})
    assert e.code == "NEXUS_CONFLICT"
    assert e.http_status == 409
    assert "name_duplicated" in str(e)


def test_409_with_expected_actual_is_project_changed():
    # 带 expected/actual 的 409 保持原行为：NEXUS_PROJECT_CHANGED。
    e = map_response_error("mint_instances", 409,
                           '{"error":"project changed","expected":"a","actual":"b"}',
                           {"error": "project changed", "expected": "a", "actual": "b"})
    assert e.code == "NEXUS_PROJECT_CHANGED"
    assert e.http_status == 409 and "a" in str(e) and "b" in str(e)


def test_503_neo4j_no_overpromise():
    e = map_response_error("get_project_ontology_graph", 503, "graph down", None)
    assert "语义图库暂不可达" in str(e) and "不影响主功能" not in str(e)


def test_timeout_retryable_only_for_reads():
    e = map_transport_error("list_instances", httpx.ReadTimeout("t"))
    assert e.code == "NEXUS_TIMEOUT" and "NEXUS_BASE_URL" in str(e)
