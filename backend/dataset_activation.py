"""Testable helpers for projecting and activating project datasets."""

import copy


def project_dataset_to_object_types(dataset, existing_types=None, demo_types=None):
    """Refresh graph fields without discarding project-owned extension fields."""
    existing_types = existing_types or {}
    demo_types = demo_types or {}

    if dataset.get("id") == "demo" or dataset.get("graph_data") is None:
        return copy.deepcopy(demo_types)

    new_types = {}
    graph_data = dataset.get("graph_data") or {}
    for node in graph_data.get("nodes", []):
        rid = node.get("rid")
        if not rid:
            continue

        old = existing_types.get(rid) or {}
        projected = copy.deepcopy(old)
        projected.update({
            "rid": rid,
            "name": node.get("name", rid),
            "category": node.get("category", "Core"),
            "description": node.get("description", ""),
            "color": node.get("color") or old.get("color", "#888888"),
            "properties": copy.deepcopy(node.get("properties", [])),
            "injected_interfaces": copy.deepcopy(
                node.get("injected_interfaces") or old.get("injected_interfaces", [])
            ),
            "asset_id": (
                node.get("asset_id")
                if node.get("asset_id") is not None
                else old.get("asset_id")
            ),
            "mock_instances": copy.deepcopy(
                node.get("mock_instances", []) or old.get("mock_instances", [])
            ),
            "source": node.get("source"),
        })
        new_types[rid] = projected
    return new_types


def activate_or_create_project(store, dataset, build_object_types):
    """Load an existing project read-only, or create a missing project once."""
    dataset_id = str(dataset.get("id") or "").strip()
    if not dataset_id or dataset_id == "demo":
        raise ValueError("a non-demo dataset id is required")

    if store.activate(dataset_id):
        return store.get_object_types(), False

    object_types = build_object_types(dataset)
    store.create_project(
        dataset.get("name") or dataset_id,
        object_types=object_types,
        project_id=dataset_id,
        dataset=dataset,
    )
    return store.get_object_types(), True
