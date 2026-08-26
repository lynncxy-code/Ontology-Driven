from .service import ArtStudioUploadError, ArtStudioUploadService


def register_artstudio_upload_routes(*args, **kwargs):
    from .api import register_artstudio_upload_routes as register

    return register(*args, **kwargs)

__all__ = [
    "ArtStudioUploadError",
    "ArtStudioUploadService",
    "register_artstudio_upload_routes",
]
