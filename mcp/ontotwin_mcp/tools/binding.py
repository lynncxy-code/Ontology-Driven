"""binding 域写工具：花名册上传（stage-write）、自动匹配（compute）、
绑定/解绑/批量绑定/铸造实例（persist-write，会修改当前激活项目）。

统一约定：expected_project_id 非空时作乐观并发校验；为空则不放进 body/data，
保持后端「缺省=旧行为」。
"""

from .. import config
from ..files import resolve_upload


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def upload_roster(file_path: str, expected_project_id: str = "") -> dict:
        """上传绑定花名册 CSV 到暂存区（stage-write，不改激活项目）。

        expected_project_id 非空时作为 form field 传给后端做乐观并发校验；
        为空则不放进表单，保持后端缺省行为。
        """
        base, content = resolve_upload(file_path, settings, allowed_ext=[".csv"])
        data = {}
        if expected_project_id:
            data["expected_project_id"] = expected_project_id
        return client.post_multipart(
            "upload_roster", "/api/v2/binding/roster/upload",
            [("file", base, content)], data=data)

    @mcp.tool()
    def automatch_bindings() -> dict:
        """按规则自动匹配组件与实例，只出建议不落库（compute，无副作用）。"""
        return client.post_json(
            "automatch_bindings", "/api/v2/binding/automatch")

    @mcp.tool()
    def bind_instance(component_id: str, instance_id: str,
                      expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目（persist-write）：把组件绑定到实例。

        expected_project_id 非空时作乐观并发校验；为空则保持后端缺省（旧）行为。
        """
        body = {"component_id": component_id, "instance_id": instance_id}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("bind_instance", "/api/v2/binding/bind", json=body)

    @mcp.tool()
    def bind_instances_batch(pairs: list, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目（persist-write）：批量绑定组件↔实例。

        pairs 为 [{component_id, instance_id}, ...]；透传后端返回 {bound, failed}。
        expected_project_id 非空时作乐观并发校验；为空则保持后端缺省行为。
        """
        body = {"pairs": pairs}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "bind_instances_batch", "/api/v2/binding/bind_batch", json=body)

    @mcp.tool()
    def unbind_instance(component_id: str, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目（persist-write）：解除组件的实例绑定。

        expected_project_id 非空时作乐观并发校验；为空则保持后端缺省（旧）行为。
        """
        body = {"component_id": component_id}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("unbind_instance", "/api/v2/binding/unbind", json=body)

    @mcp.tool()
    def mint_instances(dry_run: bool = False, expected_project_id: str = "") -> dict:
        """铸造缺失实例（dry_run=true 仅预览只读；false 时本操作会修改当前激活项目）。

        透传后端返回 {minted, to_create, to_update}。
        expected_project_id 非空时作乐观并发校验；为空则保持后端缺省行为。
        """
        body = {"dry_run": dry_run}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("mint_instances", "/api/v2/binding/mint", json=body)

    for f in (upload_roster, automatch_bindings, bind_instance,
              bind_instances_batch, unbind_instance, mint_instances):
        registry[f.__name__] = f
