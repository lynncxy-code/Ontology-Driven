"""Ontology JSON semantic validation and Cypher generation.

The JSON Schema checks shape. This module checks the ontology rules from
Lingshu-Round2/docs/ONTOLOGY.md and emits Neo4j Cypher for the same graph model.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


API_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
UUID_SUFFIX_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

RID_PREFIXES = {
    "shared_property_types": ("SharedPropertyType", "ri.shprop."),
    "interface_types": ("InterfaceType", "ri.iface."),
    "object_types": ("ObjectType", "ri.obj."),
    "link_types": ("LinkType", "ri.link."),
    "action_types": ("ActionType", "ri.action."),
}

RID_PREFIX_BY_TARGET_LABEL = {
    "SharedPropertyType": "ri.shprop.",
    "PropertyType": "ri.prop.",
    "InterfaceType": "ri.iface.",
    "ObjectType": "ri.obj.",
    "LinkType": "ri.link.",
    "ActionType": "ri.action.",
}

ROOT_FIELDS = {
    "version",
    "shared_property_types",
    "interface_types",
    "object_types",
    "link_types",
    "action_types",
}
SHARED_PROPERTY_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "lifecycle_status",
    "data_type",
}
PROPERTY_FIELDS = SHARED_PROPERTY_FIELDS | {"inherit_from_shared_property_type_rid"}
INTERFACE_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "lifecycle_status",
    "category",
    "extends_interface_type_rids",
    "required_shared_property_type_rids",
    "link_requirements",
    "object_constraint",
}
OBJECT_LINK_REQUIREMENT_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "cardinality",
    "source_object",
    "target_object",
}
LINK_OBJECT_CONSTRAINT_FIELDS = {"source_object", "target_object"}
OBJECT_TYPE_SPEC_FIELDS = {"reference_type", "object_type_rid", "interface_type_rid"}
OBJECT_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "lifecycle_status",
    "property_types",
    "implements_interface_type_rids",
    "primary_key_property_type_rids",
}
LINK_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "lifecycle_status",
    "source_object_type_rid",
    "source_interface_type_rid",
    "target_object_type_rid",
    "target_interface_type_rid",
    "property_types",
    "cardinality",
    "primary_key_property_type_rids",
    "implements_interface_type_rids",
}
ACTION_FIELDS = {
    "rid",
    "api_name",
    "display_name",
    "description",
    "lifecycle_status",
    "parameters",
    "execution",
    "safety_level",
}
ACTION_PARAMETER_FIELDS = {
    "api_name",
    "display_name",
    "description",
    "required",
    "explicit_type",
    "derived_from_object_type_rid",
    "derived_from_link_type_rid",
    "derived_from_interface_type_rid",
}
ACTION_EXECUTION_FIELDS = {
    "type",
    "is_batch",
    "is_sync",
    "native_crud_json",
    "sql_template",
}

DATA_TYPES = {
    "DT_UNKNOWN",
    "DT_STRING",
    "DT_INTEGER",
    "DT_DOUBLE",
    "DT_BOOLEAN",
    "DT_TIMESTAMP",
    "DT_DATE",
    "DT_ATTACHMENT",
}

CARDINALITIES = {
    "CARDINALITY_UNSPECIFIED",
    "ONE_TO_ONE",
    "ONE_TO_MANY",
    "MANY_TO_MANY",
}

INTERFACE_CATEGORIES = {
    "INTERFACE_CATEGORY_INVALID",
    "OBJECT_INTERFACE",
    "LINK_INTERFACE",
}

LIFECYCLE_STATUSES = {
    "LIFECYCLE_UNSPECIFIED",
    "ACTIVE",
    "EXPERIMENTAL",
    "DEPRECATED",
    "EXAMPLE",
}

ACTION_SAFETY_LEVELS = {
    "SAFETY_UNSPECIFIED",
    "SAFETY_READ_ONLY",
    "SAFETY_IDEMPOTENT_WRITE",
    "SAFETY_NON_IDEMPOTENT",
    "SAFETY_CRITICAL",
}

ENGINE_TYPES = {
    "ENGINE_UNSPECIFIED",
    "ENGINE_NATIVE_CRUD",
    "ENGINE_SQL_RUNNER",
}

REFERENCE_TYPES = {
    "REFERENCE_TYPE_INVALID",
    "SELF",
    "EXPLICIT_OBJECT",
    "EXPLICIT_INTERFACE",
}

SOURCE_FIELDS = ("source_object_type_rid", "source_interface_type_rid")
TARGET_FIELDS = ("target_object_type_rid", "target_interface_type_rid")
PARAM_SOURCE_FIELDS = (
    "explicit_type",
    "derived_from_object_type_rid",
    "derived_from_link_type_rid",
    "derived_from_interface_type_rid",
)
IMPLEMENTATION_FIELDS = (
    "native_crud_json",
    "sql_template",
)
ENGINE_IMPLEMENTATION_FIELDS = {
    "ENGINE_NATIVE_CRUD": "native_crud_json",
    "ENGINE_SQL_RUNNER": "sql_template",
}
MISSING_FIELDS_MARKER = object()


class OntologyValidationError(ValueError):
    """Raised when an ontology JSON document violates semantic rules."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=_reject_duplicate_json_keys)
    if not isinstance(data, dict):
        raise OntologyValidationError(["<root>: ontology JSON must be an object"])
    return data


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def validate_json_schema(instance: dict[str, Any], schema_path: str | Path) -> None:
    """Validate JSON shape with ontology.schema.json when jsonschema is installed."""
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - depends on host env
        raise OntologyValidationError(
            ["jsonschema package is required for --schema validation"]
        ) from exc

    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.path))
    if errors:
        rendered = []
        for err in errors:
            path = ".".join(str(part) for part in err.path) or "<root>"
            rendered.append(f"{path}: {err.message}")
        raise OntologyValidationError(rendered)


def validate_ontology(registry: dict[str, Any]) -> None:
    """Validate ontology semantic rules not expressible, or not convenient, in JSON Schema."""
    errors: list[str] = []
    ctx = _Context(registry, errors)
    ctx.validate()
    errors = collect_missing_field_errors(registry) + errors
    if errors:
        raise OntologyValidationError(errors)


def generate_cypher(registry: dict[str, Any]) -> str:
    """Generate idempotent Cypher MERGE statements for the ontology graph."""
    validate_ontology(registry)

    ctx = _Context(registry, [])
    lines: list[str] = [
        "// Generated from ontology JSON. Review before running in production.",
        "// Nodes are matched by rid.",
        "",
    ]

    def merge_node(label: str, rid: str, props: dict[str, Any]) -> None:
        node_props = {"rid": rid, **props}
        labels = f"{label}:OntologyEntity"
        key_props = {"rid": rid}
        lines.append(f"MERGE (n:{labels} {_cypher(key_props)})")
        lines.append(f"SET n += {_cypher(node_props)};")
        lines.append("")

    for rid, item in ctx.shared.items():
        merge_node("SharedPropertyType", rid, _base_props(item, extra=("data_type",)))

    for _owner_label, _owner_rid, _prop_key, prop in ctx.iter_properties():
        props = _base_props(prop, extra=("data_type",))
        merge_node("PropertyType", prop["rid"], props)

    for rid, item in ctx.interfaces.items():
        props = _base_props(item, extra=("category",))
        merge_node("InterfaceType", rid, props)

    for rid, item in ctx.objects.items():
        props = _base_props(item, extra=("primary_key_property_type_rids",))
        merge_node("ObjectType", rid, props)

    for rid, item in ctx.links.items():
        props = _base_props(item, extra=("cardinality", "primary_key_property_type_rids"))
        merge_node("LinkType", rid, props)

    for rid, item in ctx.actions.items():
        props = _base_props(item, extra=("safety_level",))
        props["parameters"] = json.dumps(
            item.get("parameters", []), ensure_ascii=False, sort_keys=True
        )
        props["execution"] = json.dumps(
            item.get("execution", {}), ensure_ascii=False, sort_keys=True
        )
        merge_node("ActionType", rid, props)

    relationship_lines = _relationship_cypher(ctx)
    if relationship_lines:
        lines.append("// Relationships")
        lines.extend(relationship_lines)

    return "\n".join(lines).rstrip() + "\n"


class _Context:
    def __init__(self, registry: dict[str, Any], errors: list[str]) -> None:
        self.registry = registry
        self.errors = errors
        self.shared = _as_dict(registry.get("shared_property_types"))
        self.interfaces = _as_dict(registry.get("interface_types"))
        self.objects = _as_dict(registry.get("object_types"))
        self.links = _as_dict(registry.get("link_types"))
        self.actions = _as_dict(registry.get("action_types"))

    def validate(self) -> None:
        self._validate_top_level()
        self._validate_shared_properties()
        self._validate_interfaces()
        self._validate_objects()
        self._validate_links()
        self._validate_actions()
        self._validate_interface_cycles()
        self._validate_inherited_link_requirement_api_names()
        self._validate_link_interface_constraint_inheritance()
        self._validate_contracts()
        self._validate_top_level_api_name_uniqueness()
        self._validate_global_rid_uniqueness()

    def iter_properties(self) -> list[tuple[str, str, str, dict[str, Any]]]:
        result: list[tuple[str, str, str, dict[str, Any]]] = []
        for owner_label, collection in (
            ("ObjectType", self.objects),
            ("LinkType", self.links),
        ):
            for owner_rid, owner in collection.items():
                if not isinstance(owner, dict):
                    continue
                for key, prop in _as_dict(owner.get("property_types")).items():
                    if isinstance(prop, dict):
                        result.append((owner_label, owner_rid, key, prop))
        return result

    def _validate_top_level(self) -> None:
        self._reject_unknown_fields(self.registry, "<root>", ROOT_FIELDS)
        _require(self.registry, "<root>", ["version"])
        self._validate_non_blank_string_field(self.registry, "<root>", "version")
        for key in RID_PREFIXES:
            if key not in self.registry:
                self.errors.append(f"{key}: missing top-level map")
            elif not isinstance(self.registry[key], dict):
                self.errors.append(f"{key}: must be an object/map")

    def _validate_shared_properties(self) -> None:
        for key, item in self.shared.items():
            path = f"shared_property_types.{key}"
            if not _is_dict(item, path, self.errors):
                continue
            self._reject_unknown_fields(item, path, SHARED_PROPERTY_FIELDS)
            self._validate_entity_common(item, path, "ri.shprop.")
            _require(item, path, ["data_type"])
            _enum(
                item.get("data_type"),
                DATA_TYPES,
                path + ".data_type",
                self.errors,
                disallow={"DT_UNKNOWN"},
            )
            self._validate_top_map_key(key, item, path)

    def _validate_interfaces(self) -> None:
        for key, item in self.interfaces.items():
            path = f"interface_types.{key}"
            if not _is_dict(item, path, self.errors):
                continue
            self._reject_unknown_fields(item, path, INTERFACE_FIELDS)
            self._validate_entity_common(item, path, "ri.iface.")
            self._validate_top_map_key(key, item, path)
            _require(item, path, ["category"])
            category = item.get("category")
            _enum(
                category,
                INTERFACE_CATEGORIES,
                path + ".category",
                self.errors,
                disallow={"INTERFACE_CATEGORY_INVALID"},
            )
            extends = self._list_field(item, "extends_interface_type_rids", path)
            self._validate_unique_values(extends, path + ".extends_interface_type_rids")
            for parent_rid in extends:
                if parent_rid == item.get("rid"):
                    self.errors.append(f"{path}.extends_interface_type_rids: cannot extend self")
                if not self._check_ref(parent_rid, self.interfaces, path, "InterfaceType"):
                    continue
                parent = self.interfaces.get(parent_rid)
                if (
                    category in {"OBJECT_INTERFACE", "LINK_INTERFACE"}
                    and isinstance(parent, dict)
                    and parent.get("category") in {"OBJECT_INTERFACE", "LINK_INTERFACE"}
                    and parent.get("category") != category
                ):
                    self.errors.append(
                        f"{path}.extends_interface_type_rids: InterfaceType may only extend same InterfaceCategory ({parent_rid})"
                    )
            required_shared = self._list_field(item, "required_shared_property_type_rids", path)
            self._validate_unique_values(required_shared, path + ".required_shared_property_type_rids")
            for shared_rid in required_shared:
                self._check_ref(shared_rid, self.shared, path, "SharedPropertyType")

            link_requirements = self._list_field(item, "link_requirements", path)
            has_object_constraint = "object_constraint" in item
            object_constraint = item.get("object_constraint")
            if category == "OBJECT_INTERFACE":
                if has_object_constraint:
                    self.errors.append(
                        f"{path}.object_constraint: only LINK_INTERFACE may define object_constraint"
                    )
                for index, requirement in enumerate(link_requirements):
                    self._validate_link_requirement(requirement, f"{path}.link_requirements[{index}]")
            elif category == "LINK_INTERFACE":
                if link_requirements:
                    self.errors.append(
                        f"{path}.link_requirements: only OBJECT_INTERFACE may define link_requirements"
                    )
                if not isinstance(object_constraint, dict):
                    self.errors.append(
                        f"{path}.object_constraint: LINK_INTERFACE must define object_constraint"
                    )
                else:
                    self._validate_link_object_constraint(object_constraint, path + ".object_constraint")

    def _validate_objects(self) -> None:
        for key, item in self.objects.items():
            path = f"object_types.{key}"
            if not _is_dict(item, path, self.errors):
                continue
            self._reject_unknown_fields(item, path, OBJECT_FIELDS)
            self._validate_entity_common(item, path, "ri.obj.")
            self._validate_top_map_key(key, item, path)
            _require(item, path, ["property_types", "primary_key_property_type_rids"])
            props = self._validate_property_map(item, path, "ObjectType")
            implements = self._list_field(item, "implements_interface_type_rids", path)
            self._validate_unique_values(implements, path + ".implements_interface_type_rids")
            for iface_rid in implements:
                if not self._check_ref(iface_rid, self.interfaces, path, "InterfaceType"):
                    continue
                iface = self.interfaces.get(iface_rid)
                if isinstance(iface, dict) and iface.get("category") != "OBJECT_INTERFACE":
                    self.errors.append(
                        f"{path}.implements_interface_type_rids: ObjectType can only implement OBJECT_INTERFACE ({iface_rid})"
                    )
            primary_keys = self._list_field(item, "primary_key_property_type_rids", path)
            self._validate_unique_values(primary_keys, path + ".primary_key_property_type_rids")
            self._validate_primary_keys(primary_keys, path, props, require_non_empty=True)

    def _validate_links(self) -> None:
        for key, item in self.links.items():
            path = f"link_types.{key}"
            if not _is_dict(item, path, self.errors):
                continue
            self._reject_unknown_fields(item, path, LINK_FIELDS)
            self._validate_entity_common(item, path, "ri.link.")
            self._validate_top_map_key(key, item, path)
            _require(item, path, ["property_types", "cardinality", "primary_key_property_type_rids"])
            _enum(
                item.get("cardinality"),
                CARDINALITIES,
                path + ".cardinality",
                self.errors,
                disallow={"CARDINALITY_UNSPECIFIED"},
            )
            _require_exactly_one(item, SOURCE_FIELDS, path + ".source_type", self.errors)
            _require_exactly_one(item, TARGET_FIELDS, path + ".target_type", self.errors)
            self._validate_endpoint_refs(item, path)
            props = self._validate_property_map(item, path, "LinkType")
            primary_keys = self._list_field(item, "primary_key_property_type_rids", path)
            self._validate_unique_values(primary_keys, path + ".primary_key_property_type_rids")
            self._validate_primary_keys(primary_keys, path, props, require_non_empty=True)
            implements = self._list_field(item, "implements_interface_type_rids", path)
            self._validate_unique_values(implements, path + ".implements_interface_type_rids")
            for iface_rid in implements:
                if not self._check_ref(iface_rid, self.interfaces, path, "InterfaceType"):
                    continue
                iface = self.interfaces.get(iface_rid)
                if isinstance(iface, dict) and iface.get("category") != "LINK_INTERFACE":
                    self.errors.append(
                        f"{path}.implements_interface_type_rids: LinkType can only implement LINK_INTERFACE ({iface_rid})"
                    )

    def _validate_actions(self) -> None:
        for key, item in self.actions.items():
            path = f"action_types.{key}"
            if not _is_dict(item, path, self.errors):
                continue
            self._reject_unknown_fields(item, path, ACTION_FIELDS)
            self._validate_entity_common(item, path, "ri.action.")
            self._validate_top_map_key(key, item, path)
            _require(item, path, ["parameters", "execution", "safety_level"])
            _enum(
                item.get("safety_level"),
                ACTION_SAFETY_LEVELS,
                path + ".safety_level",
                self.errors,
                disallow={"SAFETY_UNSPECIFIED"},
            )
            seen_params: set[str] = set()
            parameters = self._list_field(item, "parameters", path)
            has_target_parameter = False
            for index, param in enumerate(parameters):
                self._validate_action_parameter(param, f"{path}.parameters[{index}]", seen_params)
                if isinstance(param, dict) and any(
                    param.get(field) not in (None, "")
                    for field in PARAM_SOURCE_FIELDS
                    if field != "explicit_type"
                ):
                    has_target_parameter = True
            if not has_target_parameter:
                self.errors.append(
                    f"{path}.parameters: ActionType must operate on at least one ObjectType, LinkType, or InterfaceType"
                )
            self._validate_execution(item.get("execution"), path + ".execution")

    def _validate_property_map(
        self, owner: dict[str, Any], path: str, owner_label: str
    ) -> dict[str, dict[str, Any]]:
        props: dict[str, dict[str, Any]] = {}
        raw_props = owner.get("property_types")
        if not isinstance(raw_props, dict):
            self.errors.append(f"{path}.property_types: must be an object/map")
            return props
        for key, prop in raw_props.items():
            prop_path = f"{path}.property_types.{key}"
            if not _is_dict(prop, prop_path, self.errors):
                continue
            self._reject_unknown_fields(prop, prop_path, PROPERTY_FIELDS)
            self._validate_entity_common(prop, prop_path, "ri.prop.")
            _require(prop, prop_path, ["data_type"])
            _enum(
                prop.get("data_type"),
                DATA_TYPES,
                prop_path + ".data_type",
                self.errors,
                disallow={"DT_UNKNOWN"},
            )
            if key != prop.get("api_name"):
                self.errors.append(
                    f"{prop_path}: property_types map key must equal PropertyType.api_name"
                )
            if "inherit_from_shared_property_type_rid" in prop:
                inherit_rid = prop.get("inherit_from_shared_property_type_rid")
                if not self._check_ref(
                    inherit_rid,
                    self.shared,
                    prop_path + ".inherit_from_shared_property_type_rid",
                    "SharedPropertyType",
                ):
                    continue
                shared = self.shared.get(inherit_rid)
                if isinstance(shared, dict) and shared.get("data_type") != prop.get("data_type"):
                    self.errors.append(
                        f"{prop_path}.data_type: must match inherited SharedPropertyType {inherit_rid}"
                    )
            prop_rid = prop.get("rid")
            if isinstance(prop_rid, str):
                props[prop_rid] = prop
        return props

    def _validate_primary_keys(
        self,
        primary_keys: list[Any],
        path: str,
        props_by_rid: dict[str, dict[str, Any]],
        *,
        require_non_empty: bool = False,
    ) -> None:
        if require_non_empty and not primary_keys:
            self.errors.append(f"{path}.primary_key_property_type_rids: must contain at least one property RID")
        for prop_rid in primary_keys:
            if not self._validate_ref_rid(
                prop_rid, path + ".primary_key_property_type_rids", "PropertyType"
            ):
                continue
            if prop_rid not in props_by_rid:
                self.errors.append(
                    f"{path}.primary_key_property_type_rids: {prop_rid} is not a property of this entity"
                )

    def _validate_endpoint_refs(self, item: dict[str, Any], path: str) -> None:
        for field, collection, label, category_required in (
            ("source_object_type_rid", self.objects, "ObjectType", None),
            ("target_object_type_rid", self.objects, "ObjectType", None),
            ("source_interface_type_rid", self.interfaces, "InterfaceType", "OBJECT_INTERFACE"),
            ("target_interface_type_rid", self.interfaces, "InterfaceType", "OBJECT_INTERFACE"),
        ):
            if field not in item:
                continue
            rid = item.get(field)
            if not self._check_ref(rid, collection, path + "." + field, label):
                continue
            target = collection.get(rid)
            if category_required and isinstance(target, dict) and target.get("category") != category_required:
                self.errors.append(
                    f"{path}.{field}: endpoint interfaces must be OBJECT_INTERFACE ({rid})"
                )

    def _validate_action_parameter(
        self, param: Any, path: str, seen_params: set[str]
    ) -> None:
        if not _is_dict(param, path, self.errors):
            return
        self._reject_unknown_fields(param, path, ACTION_PARAMETER_FIELDS)
        _require(param, path, ["api_name", "display_name", "required"])
        self._validate_non_blank_string_field(param, path, "display_name")
        self._validate_string_field(param, path, "description")
        self._validate_bool_field(param, path, "required")
        self._validate_api_name(param, path)
        api_name = param.get("api_name")
        if isinstance(api_name, str) and api_name:
            if api_name in seen_params:
                self.errors.append(f"{path}.api_name: duplicate action parameter api_name")
            else:
                seen_params.add(api_name)
        _require_exactly_one(param, PARAM_SOURCE_FIELDS, path + ".definition_source", self.errors)
        if "explicit_type" in param:
            _enum(
                param.get("explicit_type"),
                DATA_TYPES,
                path + ".explicit_type",
                self.errors,
                disallow={"DT_UNKNOWN"},
            )
        for field, collection, label in (
            ("derived_from_object_type_rid", self.objects, "ObjectType"),
            ("derived_from_link_type_rid", self.links, "LinkType"),
            ("derived_from_interface_type_rid", self.interfaces, "InterfaceType"),
        ):
            if field in param:
                self._check_ref(param.get(field), collection, path + "." + field, label)

    def _validate_execution(self, execution: Any, path: str) -> None:
        if not _is_dict(execution, path, self.errors):
            return
        self._reject_unknown_fields(execution, path, ACTION_EXECUTION_FIELDS)
        _require(execution, path, ["type", "is_batch", "is_sync"])
        self._validate_bool_field(execution, path, "is_batch")
        self._validate_bool_field(execution, path, "is_sync")
        self._validate_non_blank_string_field(execution, path, "native_crud_json")
        self._validate_non_blank_string_field(execution, path, "sql_template")
        _enum(
            execution.get("type"),
            ENGINE_TYPES,
            path + ".type",
            self.errors,
            disallow={"ENGINE_UNSPECIFIED"},
        )
        _require_exactly_one(execution, IMPLEMENTATION_FIELDS, path + ".implementation", self.errors)
        engine_type = execution.get("type")
        expected_field = (
            ENGINE_IMPLEMENTATION_FIELDS.get(engine_type)
            if isinstance(engine_type, str)
            else None
        )
        if expected_field and execution.get(expected_field) in (None, ""):
            self.errors.append(
                f"{path}.implementation: {engine_type} requires {expected_field}"
            )

    def _validate_link_requirement(self, requirement: Any, path: str) -> None:
        if not _is_dict(requirement, path, self.errors):
            return
        self._reject_unknown_fields(requirement, path, OBJECT_LINK_REQUIREMENT_FIELDS)
        _require(
            requirement,
            path,
            ["rid", "api_name", "display_name", "cardinality", "source_object", "target_object"],
        )
        self._validate_link_requirement_rid(requirement, path)
        self._validate_non_blank_string_field(requirement, path, "display_name")
        self._validate_string_field(requirement, path, "description")
        self._validate_api_name(requirement, path)
        _enum(
            requirement.get("cardinality"),
            CARDINALITIES,
            path + ".cardinality",
            self.errors,
            disallow={"CARDINALITY_UNSPECIFIED"},
        )
        self._validate_object_type_spec(requirement.get("source_object"), path + ".source_object")
        self._validate_object_type_spec(requirement.get("target_object"), path + ".target_object")
        if not (
            isinstance(requirement.get("source_object"), dict)
            and requirement["source_object"].get("reference_type") == "SELF"
        ) and not (
            isinstance(requirement.get("target_object"), dict)
            and requirement["target_object"].get("reference_type") == "SELF"
        ):
            self.errors.append(f"{path}: ObjectLinkRequirement must reference SELF on source_object or target_object")

    def _validate_link_requirement_rid(self, requirement: dict[str, Any], path: str) -> None:
        self._validate_string_field(requirement, path, "rid")
        rid = requirement.get("rid")
        if not isinstance(rid, str):
            return
        if rid.startswith("ri.link."):
            if self._validate_ref_rid(rid, path + ".rid", "LinkType"):
                self._check_ref(rid, self.links, path + ".rid", "LinkType")
            return
        if rid.startswith("ri.iface."):
            if self._validate_ref_rid(rid, path + ".rid", "InterfaceType") and self._check_ref(
                rid, self.interfaces, path + ".rid", "InterfaceType"
            ):
                iface = self.interfaces.get(rid)
                if isinstance(iface, dict) and iface.get("category") != "LINK_INTERFACE":
                    self.errors.append(f"{path}.rid: InterfaceType must be LINK_INTERFACE")
            return
        self.errors.append(f"{path}.rid: must be a LinkType RID or LINK_INTERFACE RID")

    def _validate_link_object_constraint(self, constraint: dict[str, Any], path: str) -> None:
        self._reject_unknown_fields(constraint, path, LINK_OBJECT_CONSTRAINT_FIELDS)
        _require(constraint, path, ["source_object", "target_object"])
        self._validate_object_type_spec(constraint.get("source_object"), path + ".source_object")
        self._validate_object_type_spec(constraint.get("target_object"), path + ".target_object")
        for field in ("source_object", "target_object"):
            spec = constraint.get(field)
            if isinstance(spec, dict) and spec.get("reference_type") == "SELF":
                self.errors.append(f"{path}.{field}: LinkObjectConstraint must not use SELF")

    def _validate_object_type_spec(self, spec: Any, path: str) -> None:
        if not _is_dict(spec, path, self.errors):
            return
        self._reject_unknown_fields(spec, path, OBJECT_TYPE_SPEC_FIELDS)
        _require(spec, path, ["reference_type"])
        self._validate_string_field(spec, path, "object_type_rid")
        self._validate_string_field(spec, path, "interface_type_rid")
        reference_type = spec.get("reference_type")
        _enum(
            reference_type,
            REFERENCE_TYPES,
            path + ".reference_type",
            self.errors,
            disallow={"REFERENCE_TYPE_INVALID"},
        )
        has_obj = "object_type_rid" in spec and spec.get("object_type_rid") is not None
        has_iface = "interface_type_rid" in spec and spec.get("interface_type_rid") is not None
        if reference_type == "SELF":
            if has_obj or has_iface:
                self.errors.append(f"{path}: SELF must not set object_type_rid/interface_type_rid")
        elif reference_type == "EXPLICIT_OBJECT":
            if not has_obj or has_iface:
                self.errors.append(f"{path}: EXPLICIT_OBJECT requires only object_type_rid")
            else:
                self._check_ref(
                    spec.get("object_type_rid"),
                    self.objects,
                    path + ".object_type_rid",
                    "ObjectType",
                )
        elif reference_type == "EXPLICIT_INTERFACE":
            if not has_iface or has_obj:
                self.errors.append(f"{path}: EXPLICIT_INTERFACE requires only interface_type_rid")
            elif self._check_ref(
                spec.get("interface_type_rid"),
                self.interfaces,
                path + ".interface_type_rid",
                "InterfaceType",
            ):
                if self.interfaces[spec["interface_type_rid"]].get("category") != "OBJECT_INTERFACE":
                    self.errors.append(
                        f"{path}.interface_type_rid: endpoint interface must be OBJECT_INTERFACE"
                    )

    def _validate_interface_cycles(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(rid: str, stack: list[str]) -> None:
            if rid in visiting:
                cycle = " -> ".join(stack + [rid])
                self.errors.append(f"interface_types: EXTENDS cycle detected: {cycle}")
                return
            if rid in visited:
                return
            visiting.add(rid)
            iface = self.interfaces.get(rid)
            if not isinstance(iface, dict):
                visiting.remove(rid)
                visited.add(rid)
                return
            for parent_rid in _list(iface.get("extends_interface_type_rids")):
                if isinstance(parent_rid, str) and parent_rid in self.interfaces:
                    dfs(parent_rid, stack + [rid])
            visiting.remove(rid)
            visited.add(rid)

        for rid in self.interfaces:
            dfs(rid, [])

    def _validate_contracts(self) -> None:
        for rid, obj in self.objects.items():
            if not isinstance(obj, dict):
                continue
            inherited_shared = _covered_shared_property_rids(obj)
            for iface_rid in _list(obj.get("implements_interface_type_rids")):
                if not isinstance(iface_rid, str):
                    continue
                for required in self._required_shared_for_interface(iface_rid):
                    if required not in inherited_shared:
                        self.errors.append(
                            f"object_types.{rid}: missing required SharedPropertyType {required} for InterfaceType {iface_rid}"
                        )
                for requirement in self._link_requirements_for_interface(iface_rid):
                    if not self._object_has_required_link(rid, requirement):
                        requirement_id = requirement.get("rid") or requirement.get("api_name") or "<unknown>"
                        self.errors.append(
                            f"object_types.{rid}: missing required LinkType for ObjectLinkRequirement {requirement_id} of InterfaceType {iface_rid}"
                        )

        for rid, link in self.links.items():
            if not isinstance(link, dict):
                continue
            inherited_shared = _covered_shared_property_rids(link)
            for iface_rid in _list(link.get("implements_interface_type_rids")):
                for required in self._required_shared_for_interface(iface_rid):
                    if required not in inherited_shared:
                        self.errors.append(
                            f"link_types.{rid}: missing required SharedPropertyType {required} for InterfaceType {iface_rid}"
                        )
                for constraint_iface_rid, constraint in self._object_constraints_for_interface(iface_rid):
                    self._validate_link_matches_constraint(
                        link, constraint, f"link_types.{rid}", constraint_iface_rid
                    )

    def _validate_link_interface_constraint_inheritance(self) -> None:
        for iface_rid, iface in self.interfaces.items():
            if not isinstance(iface, dict) or iface.get("category") != "LINK_INTERFACE":
                continue
            constraint = iface.get("object_constraint")
            if not isinstance(constraint, dict):
                continue
            for parent_rid in _list(iface.get("extends_interface_type_rids")):
                for ancestor_rid, ancestor_constraint in self._object_constraints_for_interface(parent_rid):
                    if not self._link_object_constraint_satisfies(constraint, ancestor_constraint):
                        self.errors.append(
                            f"interface_types.{iface_rid}.object_constraint: does not satisfy object_constraint of parent InterfaceType {ancestor_rid}"
                        )

    def _validate_inherited_link_requirement_api_names(self) -> None:
        for iface_rid, iface in self.interfaces.items():
            if not isinstance(iface, dict) or iface.get("category") != "OBJECT_INTERFACE":
                continue
            seen_api_names: dict[str, str] = {}
            seen_rids: dict[str, str] = {}
            visited: set[str] = set()

            def visit(rid: str) -> None:
                if not isinstance(rid, str) or rid in visited or rid not in self.interfaces:
                    return
                visited.add(rid)
                current = self.interfaces[rid]
                if not isinstance(current, dict):
                    return
                for requirement in _list(current.get("link_requirements")):
                    if not isinstance(requirement, dict):
                        continue
                    api_name = requirement.get("api_name")
                    if not isinstance(api_name, str) or not api_name:
                        continue
                    if api_name in seen_api_names:
                        self.errors.append(
                            f"interface_types.{iface_rid}.link_requirements.api_name: duplicate inherited link requirement api_name {api_name!r} from {rid} and {seen_api_names[api_name]}"
                        )
                    else:
                        seen_api_names[api_name] = rid
                    requirement_rid = requirement.get("rid")
                    if not isinstance(requirement_rid, str) or not requirement_rid:
                        continue
                    if requirement_rid in seen_rids:
                        self.errors.append(
                            f"interface_types.{iface_rid}.link_requirements.rid: duplicate inherited link requirement rid {requirement_rid!r} from {rid} and {seen_rids[requirement_rid]}"
                        )
                    else:
                        seen_rids[requirement_rid] = rid
                for parent in _list(current.get("extends_interface_type_rids")):
                    if isinstance(parent, str):
                        visit(parent)

            visit(iface_rid)

    def _validate_link_matches_constraint(
        self, link: dict[str, Any], constraint: dict[str, Any], path: str, iface_rid: str
    ) -> None:
        for side, endpoint_fields in (
            ("source", SOURCE_FIELDS),
            ("target", TARGET_FIELDS),
        ):
            spec = constraint.get(f"{side}_object")
            if not isinstance(spec, dict):
                continue
            if not self._endpoint_satisfies_spec(link, endpoint_fields, spec):
                self.errors.append(
                    f"{path}: {side}_type does not satisfy object_constraint of InterfaceType {iface_rid}"
                )

    def _endpoint_satisfies_spec(
        self, link: dict[str, Any], endpoint_fields: tuple[str, str], spec: dict[str, Any]
    ) -> bool:
        ref_type = spec.get("reference_type")
        if ref_type == "SELF":
            return True
        object_field, iface_field = endpoint_fields
        endpoint_object = link.get(object_field)
        endpoint_iface = link.get(iface_field)
        if ref_type == "EXPLICIT_OBJECT":
            return endpoint_object == spec.get("object_type_rid")
        if ref_type == "EXPLICIT_INTERFACE":
            required_iface = spec.get("interface_type_rid")
            if isinstance(endpoint_iface, str) and endpoint_iface:
                return self._interface_satisfies(endpoint_iface, required_iface)
            if isinstance(endpoint_object, str) and endpoint_object in self.objects:
                return any(
                    self._interface_satisfies(impl, required_iface)
                    for impl in _list(self.objects[endpoint_object].get("implements_interface_type_rids"))
                )
        return False

    def _required_shared_for_interface(self, iface_rid: str) -> set[str]:
        result: set[str] = set()
        seen: set[str] = set()

        def visit(rid: str) -> None:
            if not isinstance(rid, str):
                return
            if rid in seen or rid not in self.interfaces:
                return
            seen.add(rid)
            iface = self.interfaces[rid]
            if not isinstance(iface, dict):
                return
            result.update(
                shared_rid
                for shared_rid in _list(iface.get("required_shared_property_type_rids"))
                if isinstance(shared_rid, str)
            )
            for parent in _list(iface.get("extends_interface_type_rids")):
                if isinstance(parent, str):
                    visit(parent)

        visit(iface_rid)
        return result

    def _link_requirements_for_interface(self, iface_rid: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        def visit(rid: str) -> None:
            if not isinstance(rid, str):
                return
            if rid in seen or rid not in self.interfaces:
                return
            seen.add(rid)
            iface = self.interfaces[rid]
            if not isinstance(iface, dict):
                return
            for requirement in _list(iface.get("link_requirements")):
                if isinstance(requirement, dict):
                    result.append(requirement)
            for parent in _list(iface.get("extends_interface_type_rids")):
                if isinstance(parent, str):
                    visit(parent)

        visit(iface_rid)
        return result

    def _object_constraints_for_interface(self, iface_rid: str) -> list[tuple[str, dict[str, Any]]]:
        result: list[tuple[str, dict[str, Any]]] = []
        seen: set[str] = set()

        def visit(rid: str) -> None:
            if not isinstance(rid, str):
                return
            if rid in seen or rid not in self.interfaces:
                return
            seen.add(rid)
            iface = self.interfaces[rid]
            if not isinstance(iface, dict):
                return
            constraint = iface.get("object_constraint")
            if isinstance(constraint, dict):
                result.append((rid, constraint))
            for parent in _list(iface.get("extends_interface_type_rids")):
                if isinstance(parent, str):
                    visit(parent)

        visit(iface_rid)
        return result

    def _object_has_required_link(self, object_rid: str, requirement: dict[str, Any]) -> bool:
        requirement_rid = requirement.get("rid")
        if isinstance(requirement_rid, str) and requirement_rid.startswith("ri.link."):
            candidates = [self.links.get(requirement_rid)]
        else:
            candidates = self.links.values()
        for link in candidates:
            if not isinstance(link, dict):
                continue
            if (
                isinstance(requirement_rid, str)
                and requirement_rid.startswith("ri.iface.")
                and not any(
                    self._interface_satisfies(impl, requirement_rid)
                    for impl in _list(link.get("implements_interface_type_rids"))
                )
            ):
                continue
            if link.get("cardinality") != requirement.get("cardinality"):
                continue
            if not self._link_endpoint_satisfies_requirement(
                object_rid, link, SOURCE_FIELDS, requirement.get("source_object")
            ):
                continue
            if self._link_endpoint_satisfies_requirement(
                object_rid, link, TARGET_FIELDS, requirement.get("target_object")
            ):
                return True
        return False

    def _link_endpoint_satisfies_requirement(
        self,
        object_rid: str,
        link: dict[str, Any],
        endpoint_fields: tuple[str, str],
        spec: Any,
    ) -> bool:
        if not isinstance(spec, dict):
            return False
        if spec.get("reference_type") == "SELF":
            return self._endpoint_accepts_object(link, endpoint_fields, object_rid)
        return self._endpoint_satisfies_spec(link, endpoint_fields, spec)

    def _endpoint_accepts_object(
        self, link: dict[str, Any], endpoint_fields: tuple[str, str], object_rid: str
    ) -> bool:
        object_field, iface_field = endpoint_fields
        if link.get(object_field) == object_rid:
            return True
        endpoint_iface = link.get(iface_field)
        obj = self.objects.get(object_rid)
        if endpoint_iface and isinstance(obj, dict):
            return any(
                self._interface_satisfies(impl, endpoint_iface)
                for impl in _list(obj.get("implements_interface_type_rids"))
            )
        return False

    def _interface_satisfies(self, candidate_rid: str, required_rid: str) -> bool:
        if not isinstance(candidate_rid, str) or not isinstance(required_rid, str):
            return False
        if candidate_rid == required_rid:
            return True
        seen: set[str] = set()

        def visit(rid: str) -> bool:
            if rid in seen or rid not in self.interfaces:
                return False
            seen.add(rid)
            iface = self.interfaces[rid]
            if not isinstance(iface, dict):
                return False
            for parent in _list(self.interfaces[rid].get("extends_interface_type_rids")):
                if parent == required_rid or (isinstance(parent, str) and visit(parent)):
                    return True
            return False

        return visit(candidate_rid)

    def _link_object_constraint_satisfies(
        self, candidate: dict[str, Any], required: dict[str, Any]
    ) -> bool:
        return all(
            self._object_type_spec_satisfies(
                candidate.get(f"{side}_object"),
                required.get(f"{side}_object"),
            )
            for side in ("source", "target")
        )

    def _object_type_spec_satisfies(self, candidate: Any, required: Any) -> bool:
        if not isinstance(candidate, dict) or not isinstance(required, dict):
            return False
        candidate_type = candidate.get("reference_type")
        required_type = required.get("reference_type")
        if required_type == "EXPLICIT_OBJECT":
            return (
                candidate_type == "EXPLICIT_OBJECT"
                and candidate.get("object_type_rid") == required.get("object_type_rid")
            )
        if required_type == "EXPLICIT_INTERFACE":
            required_iface = required.get("interface_type_rid")
            if candidate_type == "EXPLICIT_INTERFACE":
                return self._interface_satisfies(
                    candidate.get("interface_type_rid"), required_iface
                )
            if candidate_type == "EXPLICIT_OBJECT":
                object_rid = candidate.get("object_type_rid")
                if not isinstance(object_rid, str):
                    return False
                obj = self.objects.get(object_rid)
                if not isinstance(obj, dict):
                    return False
                return any(
                    self._interface_satisfies(impl, required_iface)
                    for impl in _list(obj.get("implements_interface_type_rids"))
                )
        return False

    def _validate_global_rid_uniqueness(self) -> None:
        seen: dict[str, str] = {}
        for map_name, collection in (
            ("shared_property_types", self.shared),
            ("interface_types", self.interfaces),
            ("object_types", self.objects),
            ("link_types", self.links),
            ("action_types", self.actions),
        ):
            for key, item in collection.items():
                if isinstance(item, dict):
                    self._remember_rid(seen, item.get("rid"), f"{map_name}.{key}")
        for owner_label, owner_rid, prop_key, prop in self.iter_properties():
            self._remember_rid(seen, prop.get("rid"), f"{owner_label}.{owner_rid}.property_types.{prop_key}")

    def _validate_top_level_api_name_uniqueness(self) -> None:
        for map_name, collection in (
            ("shared_property_types", self.shared),
            ("interface_types", self.interfaces),
            ("object_types", self.objects),
            ("link_types", self.links),
            ("action_types", self.actions),
        ):
            self._validate_unique_api_names(collection, f"{map_name}.api_name")
        for iface_rid, iface in self.interfaces.items():
            if isinstance(iface, dict):
                requirements = [
                    requirement
                    for requirement in _list(iface.get("link_requirements"))
                    if isinstance(requirement, dict)
                ]
                self._validate_unique_api_names(
                    requirements,
                    f"interface_types.{iface_rid}.link_requirements.api_name",
                )

    def _validate_unique_api_names(self, items: Any, path: str) -> None:
        seen: dict[str, str] = {}
        iterable = items.values() if isinstance(items, dict) else items
        for index, item in enumerate(iterable):
            if not isinstance(item, dict):
                continue
            api_name = item.get("api_name")
            if not isinstance(api_name, str) or not api_name:
                continue
            item_id = item.get("rid") or str(index)
            if api_name in seen:
                self.errors.append(
                    f"{path}: duplicate api_name {api_name!r} used by {item_id} and {seen[api_name]}"
                )
            else:
                seen[api_name] = item_id

    def _remember_rid(self, seen: dict[str, str], rid: Any, path: str) -> None:
        if not isinstance(rid, str) or not rid:
            return
        if rid in seen:
            self.errors.append(f"{path}.rid: duplicate RID also used at {seen[rid]}")
        else:
            seen[rid] = path

    def _validate_entity_common(self, item: dict[str, Any], path: str, prefix: str) -> None:
        _require(item, path, ["rid", "api_name", "display_name", "lifecycle_status"])
        self._validate_rid_field(item, path, prefix)
        self._validate_non_blank_string_field(item, path, "display_name")
        self._validate_string_field(item, path, "description")
        self._validate_api_name(item, path)
        _enum(
            item.get("lifecycle_status"),
            LIFECYCLE_STATUSES,
            path + ".lifecycle_status",
            self.errors,
            disallow={"LIFECYCLE_UNSPECIFIED"},
        )

    def _validate_rid_field(self, item: dict[str, Any], path: str, prefix: str) -> None:
        self._validate_string_field(item, path, "rid")
        rid = item.get("rid")
        if not isinstance(rid, str):
            return
        if not rid.startswith(prefix) or len(rid) <= len(prefix):
            self.errors.append(f"{path}.rid: must start with {prefix}")
            return
        if not UUID_SUFFIX_RE.match(rid[len(prefix):]):
            self.errors.append(f"{path}.rid: must match {prefix}<uuid>")

    def _reject_unknown_fields(self, item: dict[str, Any], path: str, allowed: set[str]) -> None:
        unknown = sorted(
            str(key)
            for key in item
            if key is not MISSING_FIELDS_MARKER and key not in allowed
        )
        if unknown:
            self.errors.append(f"{path}: unknown field(s): {', '.join(unknown)}")

    def _validate_ref_rid(self, rid: Any, path: str, target_label: str) -> bool:
        if not isinstance(rid, str):
            self.errors.append(f"{path}: must be a {target_label} RID string")
            return False
        prefix = RID_PREFIX_BY_TARGET_LABEL[target_label]
        if not rid.startswith(prefix) or len(rid) <= len(prefix):
            self.errors.append(f"{path}: must start with {prefix}")
            return False
        if not UUID_SUFFIX_RE.match(rid[len(prefix):]):
            self.errors.append(f"{path}: must match {prefix}<uuid>")
            return False
        return True

    def _validate_api_name(self, item: dict[str, Any], path: str) -> None:
        api_name = item.get("api_name")
        if not isinstance(api_name, str) or not API_NAME_RE.match(api_name):
            self.errors.append(
                f"{path}.api_name: must be snake_case, start with a letter, and not end with '_'"
            )

    def _validate_top_map_key(self, key: str, item: dict[str, Any], path: str) -> None:
        if key != item.get("rid"):
            self.errors.append(f"{path}: top-level map key must equal rid")

    def _check_ref(
        self, rid: Any, collection: dict[str, Any], path: str, target_label: str
    ) -> bool:
        if not self._validate_ref_rid(rid, path, target_label):
            return False
        if rid not in collection:
            self.errors.append(f"{path}: unknown {target_label} reference {rid!r}")
            return False
        return True

    def _validate_string_field(self, item: dict[str, Any], path: str, field: str) -> None:
        if field not in item:
            return
        if not isinstance(item[field], str):
            self.errors.append(f"{path}.{field}: must be a string")

    def _validate_non_blank_string_field(self, item: dict[str, Any], path: str, field: str) -> None:
        self._validate_string_field(item, path, field)
        if isinstance(item.get(field), str) and not item[field].strip():
            self.errors.append(f"{path}.{field}: must not be blank")

    def _validate_bool_field(self, item: dict[str, Any], path: str, field: str) -> None:
        if field not in item:
            return
        if not isinstance(item[field], bool):
            self.errors.append(f"{path}.{field}: must be a boolean")

    def _list_field(self, item: dict[str, Any], field: str, path: str) -> list[Any]:
        if field not in item:
            return []
        value = item.get(field)
        if isinstance(value, list):
            return value
        self.errors.append(f"{path}.{field}: must be an array/list")
        return []

    def _validate_unique_values(self, values: list[Any], path: str) -> None:
        seen: set[str] = set()
        for value in values:
            key = repr(value)
            if key in seen:
                self.errors.append(f"{path}: duplicate value {value!r}")
            else:
                seen.add(key)


def _relationship_cypher(ctx: _Context) -> list[str]:
    lines: list[str] = []

    def rel(from_label: str, from_rid: str, rel_type: str, to_label: str, to_rid: str) -> None:
        lines.append(_merge_relationship(from_label, from_rid, rel_type, to_label, to_rid))
        lines.append("")

    for owner_label, owner_rid, _prop_key, prop in ctx.iter_properties():
        prop_rid = prop["rid"]
        rel("PropertyType", prop_rid, "BELONGS_TO", owner_label, owner_rid)
        inherit_rid = prop.get("inherit_from_shared_property_type_rid")
        if inherit_rid:
            rel("PropertyType", prop_rid, "BASED_ON", "SharedPropertyType", inherit_rid)

    for iface_rid, iface in ctx.interfaces.items():
        for parent_rid in _list(iface.get("extends_interface_type_rids")):
            rel("InterfaceType", iface_rid, "EXTENDS", "InterfaceType", parent_rid)
        for shared_rid in _list(iface.get("required_shared_property_type_rids")):
            rel("InterfaceType", iface_rid, "REQUIRES", "SharedPropertyType", shared_rid)

    for obj_rid, obj in ctx.objects.items():
        for iface_rid in _list(obj.get("implements_interface_type_rids")):
            rel("ObjectType", obj_rid, "IMPLEMENTS", "InterfaceType", iface_rid)

    for link_rid, link in ctx.links.items():
        for iface_rid in _list(link.get("implements_interface_type_rids")):
            rel("LinkType", link_rid, "IMPLEMENTS", "InterfaceType", iface_rid)
        source_label, source_rid = _endpoint_label_rid(link, source=True)
        target_label, target_rid = _endpoint_label_rid(link, source=False)
        rel(source_label, source_rid, "CONNECTS", "LinkType", link_rid)
        rel("LinkType", link_rid, "CONNECTS", target_label, target_rid)

    for action_rid, action in ctx.actions.items():
        seen_targets: set[tuple[str, str]] = set()
        for param in _list(action.get("parameters")):
            if not isinstance(param, dict):
                continue
            target = _action_target(param)
            if target and target not in seen_targets:
                seen_targets.add(target)
                label, rid = target
                rel("ActionType", action_rid, "OPERATES_ON", label, rid)

    return lines


def _merge_relationship(
    from_label: str,
    from_rid: str,
    rel_type: str,
    to_label: str,
    to_rid: str,
) -> str:
    left = _match_node("a", from_label, from_rid)
    right = _match_node("b", to_label, to_rid)
    return f"{left}\n{right}\nMERGE (a)-[r:{rel_type}]->(b);"


def _match_node(alias: str, label: str, rid: str) -> str:
    props = {"rid": rid}
    return f"MATCH ({alias}:{label} {_cypher(props)})"


def _endpoint_label_rid(link: dict[str, Any], *, source: bool) -> tuple[str, str]:
    if source:
        if "source_object_type_rid" in link:
            return ("ObjectType", link["source_object_type_rid"])
        return ("InterfaceType", link["source_interface_type_rid"])
    if "target_object_type_rid" in link:
        return ("ObjectType", link["target_object_type_rid"])
    return ("InterfaceType", link["target_interface_type_rid"])


def _action_target(param: dict[str, Any]) -> tuple[str, str] | None:
    if "derived_from_object_type_rid" in param:
        return ("ObjectType", param["derived_from_object_type_rid"])
    if "derived_from_link_type_rid" in param:
        return ("LinkType", param["derived_from_link_type_rid"])
    if "derived_from_interface_type_rid" in param:
        return ("InterfaceType", param["derived_from_interface_type_rid"])
    return None


def _base_props(item: dict[str, Any], *, extra: tuple[str, ...] = ()) -> dict[str, Any]:
    keys = ("rid", "api_name", "display_name", "description", "lifecycle_status") + extra
    return {key: item[key] for key in keys if key in item and item[key] is not None}


def _cypher(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(_cypher(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            parts.append(f"{_cypher_key(str(key))}: {_cypher(value[key])}")
        return "{" + ", ".join(parts) + "}"
    raise TypeError(f"Unsupported Cypher literal type: {type(value).__name__}")


def _cypher_key(key: str) -> str:
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return key
    return "`" + key.replace("`", "``") + "`"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _is_dict(value: Any, path: str, errors: list[str]) -> bool:
    if isinstance(value, dict):
        return True
    errors.append(f"{path}: must be an object")
    return False


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []




def _require(item: dict[str, Any], path: str, fields: list[str]) -> None:
    missing = [field for field in fields if field not in item or item[field] in (None, "")]
    if missing:
        raise_marker = item.setdefault(MISSING_FIELDS_MARKER, [])
        raise_marker.extend(missing)


def _enum(
    value: Any,
    allowed: set[str],
    path: str,
    errors: list[str],
    *,
    disallow: set[str] | None = None,
) -> None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{path}: invalid enum value {value!r}")
    elif disallow and value in disallow:
        errors.append(f"{path}: {value!r} is not allowed here")


def _require_exactly_one(
    item: dict[str, Any], fields: tuple[str, ...], path: str, errors: list[str]
) -> None:
    present = [field for field in fields if field in item and item[field] is not None]
    if len(present) != 1:
        errors.append(f"{path}: exactly one of {', '.join(fields)} must be set")


def _covered_shared_property_rids(entity: dict[str, Any]) -> set[str]:
    result = set()
    for prop in _as_dict(entity.get("property_types")).values():
        if isinstance(prop, dict):
            shared_rid = prop.get("inherit_from_shared_property_type_rid")
            if isinstance(shared_rid, str) and shared_rid:
                result.add(shared_rid)
    return result


def collect_missing_field_errors(registry: dict[str, Any]) -> list[str]:
    """Collect and remove internal missing-field markers from validate helpers."""
    errors: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            missing = value.pop(MISSING_FIELDS_MARKER, None)
            if missing:
                rendered_path = path or "<root>"
                errors.append(
                    f"{rendered_path}: missing required field(s): {', '.join(missing)}"
                )
            for key, child in list(value.items()):
                walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(registry, "")
    return errors


def build_validate_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ontology JSON.")
    parser.add_argument("json_file", help="Ontology JSON file to validate")
    parser.add_argument(
        "--schema",
        default="ontology.schema.json",
        help="JSON Schema file. Use --skip-schema to disable.",
    )
    parser.add_argument("--skip-schema", action="store_true", help="Only run ontology semantic rules")
    parser.add_argument("--quiet", action="store_true", help="Print only errors")
    return parser


def build_cypher_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Neo4j Cypher from ontology JSON.")
    parser.add_argument("json_file", help="Ontology JSON file")
    parser.add_argument("--schema", default="ontology.schema.json", help="JSON Schema file")
    parser.add_argument("--skip-schema", action="store_true", help="Skip JSON Schema validation")
    parser.add_argument("-o", "--output", help="Output .cypher path. Defaults to stdout.")
    return parser
