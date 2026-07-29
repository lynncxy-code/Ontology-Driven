import httpx
import pytest

from ontotwin_mcp.errors import NexusError


def test_get_ok(make_client):
    def h(req):
        assert req.url.path == "/api/v2/instances"
        return httpx.Response(200, json=[{"id": "i1"}])
    c = make_client(h)
    assert c.get("list_instances", "/api/v2/instances") == [{"id": "i1"}]


def test_post_json_409_maps(make_client):
    def h(req):
        return httpx.Response(409, json={"error": "project changed", "expected": "a", "actual": "b"})
    c = make_client(h)
    with pytest.raises(NexusError) as e:
        c.post_json("mint_instances", "/api/v2/binding/mint", json={"dry_run": False})
    assert e.value.http_status == 409


def test_multipart_sends_file(make_client):
    seen = {}
    def h(req):
        seen["ct"] = req.headers.get("content-type", "")
        return httpx.Response(200, json={"status": "ok"})
    c = make_client(h)
    c.post_multipart("upload_roster", "/api/v2/binding/roster/upload",
                     files=[("file", "roster.csv", b"x")], data={"expected_project_id": "p"})
    assert "multipart/form-data" in seen["ct"]


def test_multipart_timeout_override(make_client):
    def h(req):
        return httpx.Response(200, json={"status": "ok"})
    c = make_client(h)
    # 传入 timeout 覆盖默认 upload 超时，不应报错
    assert c.post_multipart("parse_cad_dxf", "/api/v2/coord/parse",
                            files=[("file", "a.dxf", b"0")], timeout=120.0) == {"status": "ok"}


def test_connect_error_maps(make_client):
    def h(req):
        raise httpx.ConnectError("refused")
    c = make_client(h)
    with pytest.raises(NexusError) as e:
        c.get("list_projects", "/api/v2/ontology/datasets")
    assert e.value.code == "NEXUS_UNREACHABLE"
