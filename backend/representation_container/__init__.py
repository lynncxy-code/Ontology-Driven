"""ObjectType-scoped Blueprint representation container capability."""


def register_representation_container_routes(*args, **kwargs):
    from .api import register_representation_container_routes as register
    return register(*args, **kwargs)


from .service import resolve_effective_container

__all__ = ["register_representation_container_routes", "resolve_effective_container"]
