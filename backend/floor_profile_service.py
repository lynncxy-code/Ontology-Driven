"""Project-level floor height configuration and atomic Z re-derivation."""

import copy
import math
import time

from coord_transform import apply_transform, canonical_to_ue


class FloorProfileError(ValueError):
    def __init__(self, code, message, status=400, fields=None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.fields = fields or {}


def _floor_number(value, field="floor"):
    if isinstance(value, bool):
        raise FloorProfileError("floor_invalid", f"{field} 必须是 1～10000 的整数")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise FloorProfileError("floor_invalid", f"{field} 必须是 1～10000 的整数") from exc
    if number < 1 or number > 10000 or str(value).strip() not in {str(number), f"{number}.0"}:
        raise FloorProfileError("floor_invalid", f"{field} 必须是 1～10000 的整数")
    return number


def _finite(value, field, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FloorProfileError("height_invalid", f"{field} 必须是有限数值")
    number = float(value)
    if not math.isfinite(number):
        raise FloorProfileError("height_invalid", f"{field} 必须是有限数值")
    return number


def _scale(profile):
    value = ((profile or {}).get("ue_transform") or {}).get("scale_to_cm", 0.1)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.1
    return number if math.isfinite(number) else 0.1


def _floor_bases(profile):
    result = {}
    for item in (profile or {}).get("floor_table") or []:
        if not isinstance(item, dict):
            continue
        try:
            floor = _floor_number(item.get("floor"))
            result[floor] = _finite(item.get("z_base_mm", 0.0), "z_base_mm")
        except FloorProfileError:
            continue
    return result


def _profile_geometry(profile):
    transform = copy.deepcopy((profile or {}).get("ue_transform") or {})
    transform.pop("display", None)
    return {
        "canonical_origin": copy.deepcopy((profile or {}).get("canonical_origin") or [0.0, 0.0]),
        "ue_transform": transform,
    }


class FloorProfileService:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _validate_floor_table(value):
        if not isinstance(value, list) or not value:
            raise FloorProfileError("floor_table_invalid", "楼层表至少需要一个楼层")

        floors = set()
        floor_ids = set()
        normalized = []
        for index, raw in enumerate(value):
            if not isinstance(raw, dict):
                raise FloorProfileError(
                    "floor_table_invalid", f"floor_table[{index}] 必须是对象"
                )
            item = copy.deepcopy(raw)
            floor = _floor_number(item.get("floor"), f"floor_table[{index}].floor")
            floor_id = str(item.get("floor_id") or f"floor-{floor}").strip()
            if not floor_id:
                raise FloorProfileError("floor_id_invalid", "floor_id 不能为空")
            if floor in floors or floor_id in floor_ids:
                raise FloorProfileError(
                    "floor_conflict",
                    f"楼层编号 {floor} 或楼层标识 {floor_id} 重复",
                    status=409,
                )
            floors.add(floor)
            floor_ids.add(floor_id)
            item["floor"] = floor
            item["floor_id"] = floor_id
            item["z_base_mm"] = _finite(item.get("z_base_mm", 0.0), "z_base_mm")
            if "ue_ground_z_cm" in item:
                item["ue_ground_z_cm"] = _finite(
                    item.get("ue_ground_z_cm"), "ue_ground_z_cm", allow_none=True
                )
            else:
                item["ue_ground_z_cm"] = None
            item.setdefault("ue_level", "")
            item.setdefault("map_codes", [])
            normalized.append(item)
        return normalized

    @staticmethod
    def _usage(project, floor, floor_id):
        components = [
            comp for comp in (project.get("components") or {}).values()
            if isinstance(comp, dict) and comp.get("floor", 1) == floor
        ]
        instances = project.get("instances") or {}
        bound_instances = sum(
            1 for comp in components
            if comp.get("bound_instance_id") in instances
        )
        frames = sum(
            1 for frame in project.get("frames") or []
            if isinstance(frame, dict)
            and (frame.get("floor_id") == floor_id or frame.get("floor") == floor)
        )
        return {
            "components": len(components),
            "bound_instances": bound_instances,
            "frames": frames,
        }

    @classmethod
    def _public_floor(cls, project, item):
        value = copy.deepcopy(item)
        value["default_component_ue_z_cm"] = round(
            float(value.get("z_base_mm") or 0.0) * _scale(project.get("spatial_profile") or {}),
            4,
        )
        value["usage"] = cls._usage(project, value["floor"], value["floor_id"])
        return value

    def list_floors(self):
        project = self.store.get_active_copy()
        if not project:
            raise FloorProfileError("no_active_project", "当前无激活项目")
        profile = project.get("spatial_profile") or {}
        floors = self._validate_floor_table(profile.get("floor_table") or [])
        return {
            "project_id": project.get("id"),
            "scale_to_cm": _scale(profile),
            "floors": [self._public_floor(project, item) for item in floors],
        }

    @staticmethod
    def _component_xy(component, profile):
        canonical = component.get("canonical_xy")
        if canonical is None:
            cad = component.get("cad_xy") or [0.0, 0.0]
            origin = (profile.get("canonical_origin") or [0.0, 0.0])[:2]
            canonical = [
                float(cad[0]) - float(origin[0]),
                float(cad[1]) - float(origin[1]),
            ]
            component["canonical_xy"] = canonical
        source_matrix = component.get("to_ue_matrix")
        if source_matrix:
            ue_xy = apply_transform(source_matrix, canonical)
            return [ue_xy[0], ue_xy[1]]
        ue = canonical_to_ue(profile, canonical, component.get("floor", 1))
        return [ue[0], ue[1]]

    @classmethod
    def _rederive_working(
        cls,
        working,
        old_profile,
        new_profile,
        changed_floor_bases,
        rederive_xy,
    ):
        old_bases = _floor_bases(old_profile)
        new_bases = _floor_bases(new_profile)
        scale = _scale(new_profile)
        instances = working.get("instances") or {}
        changed_components = []
        bound_instances = set()
        warnings = []
        now = time.time()

        for component_id, component in (working.get("components") or {}).items():
            if not isinstance(component, dict):
                continue
            try:
                floor = int(component.get("floor", 1))
            except (TypeError, ValueError):
                floor = 1
            old_base = old_bases.get(floor, 0.0)
            new_base = new_bases.get(floor, 0.0)
            if floor not in new_bases:
                warnings.append({
                    "code": "component_floor_unconfigured",
                    "component_id": component_id,
                    "floor": floor,
                })

            canonical_z = component.get("canonical_z")
            if canonical_z is None:
                canonical_z = old_base
            else:
                try:
                    canonical_z = float(canonical_z)
                except (TypeError, ValueError):
                    canonical_z = old_base

            floor_rebased = floor in changed_floor_bases
            if floor_rebased:
                canonical_z = new_base + (canonical_z - old_base)
                component["canonical_z"] = canonical_z
            elif component.get("canonical_z") is None:
                component["canonical_z"] = new_base
                canonical_z = new_base

            if rederive_xy or component.get("ue_xy") is None:
                component["ue_xy"] = cls._component_xy(component, new_profile)

            new_ue_z = round(float(canonical_z) * scale, 2)
            z_changed = component.get("ue_z") != new_ue_z
            component["ue_z"] = new_ue_z

            if floor_rebased or rederive_xy or z_changed:
                changed_components.append(component_id)
                instance_id = component.get("bound_instance_id")
                instance = instances.get(instance_id)
                if instance:
                    raw = dict(instance.get("raw_state") or {})
                    ue_xy = component.get("ue_xy") or [0.0, 0.0]
                    raw.update({
                        "translation_x": ue_xy[0],
                        "translation_y": ue_xy[1],
                        "translation_z": new_ue_z,
                        "rotation_z": float(component.get("rotation") or 0.0),
                    })
                    instance["raw_state"] = raw
                    instance["last_seen"] = now
                    bound_instances.add(instance_id)

        return {
            "components": len(changed_components),
            "bound_instances": len(bound_instances),
            "warnings": warnings,
        }

    def update_floor(self, floor_value, payload, expected_project_id=None):
        if not isinstance(payload, dict):
            raise FloorProfileError("invalid_request", "请求体必须是对象")
        floor = _floor_number(floor_value)
        if "z_base_mm" not in payload:
            raise FloorProfileError("z_base_required", "请填写规范楼层标高")
        z_base = _finite(payload.get("z_base_mm"), "z_base_mm")
        ground_provided = "ue_ground_z_cm" in payload
        ground = _finite(
            payload.get("ue_ground_z_cm"), "ue_ground_z_cm", allow_none=True
        ) if ground_provided else None

        def apply(working):
            profile = copy.deepcopy(working.get("spatial_profile") or {})
            old_profile = copy.deepcopy(profile)
            floors = self._validate_floor_table(profile.get("floor_table") or [])
            target = next((item for item in floors if item.get("floor") == floor), None)
            created = target is None
            if target is None:
                target = {
                    "floor": floor,
                    "floor_id": f"floor-{floor}",
                    "z_base_mm": z_base,
                    "ue_ground_z_cm": ground if ground_provided else None,
                    "ue_level": "",
                    "map_codes": [],
                }
                floors.append(target)
            old_base = float(target.get("z_base_mm") or 0.0)
            old_ground = target.get("ue_ground_z_cm")
            target["z_base_mm"] = z_base
            if ground_provided:
                target["ue_ground_z_cm"] = ground
            floors = self._validate_floor_table(floors)
            profile["floor_table"] = floors
            working["spatial_profile"] = profile

            base_changed = created or old_base != z_base
            affected = self._rederive_working(
                working,
                old_profile,
                profile,
                {floor} if base_changed else set(),
                False,
            ) if base_changed else {"components": 0, "bound_instances": 0, "warnings": []}
            current = next(item for item in floors if item.get("floor") == floor)
            public = self._public_floor(working, current)
            return {
                "status": "ok",
                "project_id": working.get("id"),
                "floor": public,
                "changed": {
                    "z_base_mm": base_changed,
                    "ue_ground_z_cm": ground_provided and old_ground != ground,
                },
                "affected": {
                    "components": affected["components"],
                    "bound_instances": affected["bound_instances"],
                },
                "warnings": affected["warnings"],
            }

        return self.store.transact_expected_active(expected_project_id, apply)
    def update_profile(self, payload, expected_project_id=None):
        """Compatibility path for PUT /spatial/profile, kept atomic."""
        if not isinstance(payload, dict):
            raise FloorProfileError("invalid_request", "请求体必须是对象")

        def apply(working):
            profile = copy.deepcopy(working.get("spatial_profile") or {})
            old_profile = copy.deepcopy(profile)
            if "ue_transform" in payload:
                patch = payload.get("ue_transform")
                if not isinstance(patch, dict):
                    raise FloorProfileError("ue_transform_invalid", "ue_transform 必须是对象")
                transform = profile.get("ue_transform") or {}
                transform.update(copy.deepcopy(patch))
                profile["ue_transform"] = transform
            if "floor_table" in payload:
                profile["floor_table"] = self._validate_floor_table(payload.get("floor_table"))
            if "canonical_origin" in payload:
                origin = payload.get("canonical_origin")
                if not isinstance(origin, list) or len(origin) < 2:
                    raise FloorProfileError("canonical_origin_invalid", "canonical_origin 必须包含 X、Y")
                profile["canonical_origin"] = [
                    _finite(origin[0], "canonical_origin[0]"),
                    _finite(origin[1], "canonical_origin[1]"),
                ]

            old_bases = _floor_bases(old_profile)
            new_bases = _floor_bases(profile)
            changed_floors = {
                floor for floor in set(old_bases) | set(new_bases)
                if old_bases.get(floor, 0.0) != new_bases.get(floor, 0.0)
            }
            geometry_changed = _profile_geometry(old_profile) != _profile_geometry(profile)
            working["spatial_profile"] = profile
            affected = self._rederive_working(
                working,
                old_profile,
                profile,
                changed_floors,
                geometry_changed,
            ) if changed_floors or geometry_changed else {
                "components": 0,
                "bound_instances": 0,
                "warnings": [],
            }
            return {
                "status": "ok",
                "profile": copy.deepcopy(profile),
                "affected": {
                    "components": affected["components"],
                    "bound_instances": affected["bound_instances"],
                },
                "warnings": affected["warnings"],
            }

        return self.store.transact_expected_active(expected_project_id, apply)
