from .service import resolve_effective_model


def register_instance_model_binding_routes(*args, **kwargs):
    # Keep pure resolver/service imports usable in maintenance scripts without Flask.
    from .api import register_instance_model_binding_routes as register
    return register(*args, **kwargs)


__all__ = ["register_instance_model_binding_routes", "resolve_effective_model"]
