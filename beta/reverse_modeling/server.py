from __future__ import annotations

import argparse
import cgi
import json
import mimetypes
import os
import shutil
import threading
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


APP_ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = APP_ROOT / "runtime"
UPLOAD_ROOT = RUNTIME_ROOT / "uploads"
RESULT_ROOT = RUNTIME_ROOT / "results"
DEFAULT_BACKEND = "http://127.0.0.1:8081"
HUNYUAN_SOURCE = Path(r"D:\AI\Hunyuan3D-2.1-local\src\Hunyuan3D-2.1-main")
HUNYUAN_MULTIVIEW_OUTPUT = Path(r"D:\AI\Hunyuan3D-2.1-local\output\multiview")
EXAMPLE_ROOT = HUNYUAN_SOURCE / "assets" / "example_images"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_MULTIVIEW_REQUEST_BYTES = MAX_UPLOAD_BYTES * 4 + 2 * 1024 * 1024
ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_EXPORT_TYPES = {"glb", "obj", "ply", "stl"}
VIEW_KEYS = ("front", "back", "left", "right")

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
CLIENT_CALL_LOCK = threading.Lock()
BACKEND_URL = DEFAULT_BACKEND


def now_ms() -> int:
    return int(time.time() * 1000)


def safe_number(value, default, minimum, maximum, integer=False):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = float(default)
    parsed = max(float(minimum), min(float(maximum), parsed))
    return int(round(parsed)) if integer else parsed


def backend_health() -> dict:
    config_url = BACKEND_URL.rstrip("/") + "/config"
    try:
        request = Request(config_url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        endpoints = [item.get("api_name") for item in payload.get("dependencies", []) if item.get("api_name")]
        required = {"shape_generation", "generation_all", "on_export_click"}
        endpoints_ready = required.issubset(set(endpoints))
        component_labels = {
            str((item.get("props") or {}).get("label") or "").strip().lower()
            for item in payload.get("components", [])
        }
        title = str(payload.get("title") or "")
        multiview_ready = {"front", "back", "left", "right"}.issubset(component_labels) or "2mv" in title.lower()
        online = endpoints_ready and multiview_ready
        if online:
            message = "本地多视图生成服务已连接"
        elif endpoints_ready:
            message = "当前连接的是单图服务，请启动 Hunyuan3D-2mv"
        else:
            message = "生成服务缺少必要接口"
        return {
            "online": online,
            "backend": BACKEND_URL,
            "gradio_version": payload.get("version"),
            "endpoints": endpoints,
            "mode": "multiview" if multiview_ready else "single",
            "message": message,
        }
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "online": False,
            "backend": BACKEND_URL,
            "gradio_version": None,
            "endpoints": [],
            "mode": None,
            "message": "本地多视图生成服务未连接",
            "detail": str(error),
        }


def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)


def create_job(kind: str, source_job_id: str | None = None) -> dict:
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "kind": kind,
        "source_job_id": source_job_id,
        "status": "queued",
        "status_text": "等待本地生成服务",
        "created_at": now_ms(),
        "updated_at": now_ms(),
        "result": None,
        "error": None,
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    return job


def update_job(job_id: str, **changes) -> None:
    with JOBS_LOCK:
        if job_id not in JOBS:
            return
        JOBS[job_id].update(changes)
        JOBS[job_id]["updated_at"] = now_ms()


def public_job(job: dict) -> dict:
    return {
        "id": job.get("id"),
        "kind": job.get("kind"),
        "source_job_id": job.get("source_job_id"),
        "status": job.get("status"),
        "status_text": job.get("status_text"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "result": job.get("result"),
        "error": job.get("error"),
    }


def resolve_result_path(source) -> Path | None:
    """Extract a local file path from Gradio filepath, FileData, or gr.update output."""
    if not source:
        return None
    if isinstance(source, Path):
        source_path = source
    elif isinstance(source, str):
        source_path = Path(source)
    elif isinstance(source, dict):
        for key in ("path", "value", "name"):
            if source.get(key):
                source_path = resolve_result_path(source[key])
                if source_path:
                    return source_path
        return None
    else:
        for attribute in ("path", "value", "name"):
            candidate = getattr(source, attribute, None)
            if candidate:
                source_path = resolve_result_path(candidate)
                if source_path:
                    return source_path
        return None
    return source_path if source_path.is_file() else None


def copy_result_file(source, job_id: str, preferred_name: str) -> str | None:
    source_path = resolve_result_path(source)
    if not source_path:
        return None
    job_root = RESULT_ROOT / job_id
    job_root.mkdir(parents=True, exist_ok=True)
    suffix = source_path.suffix.lower()
    target_name = preferred_name if Path(preferred_name).suffix else preferred_name + suffix
    target = job_root / target_name
    shutil.copy2(source_path, target)
    return str(target)


def recover_latest_result() -> dict:
    if not HUNYUAN_MULTIVIEW_OUTPUT.is_dir():
        raise RuntimeError("没有找到多视图模型输出目录。")
    result_dirs = [
        item for item in HUNYUAN_MULTIVIEW_OUTPUT.iterdir()
        if item.is_dir() and (item / "white_mesh.glb").is_file()
    ]
    textured_dirs = [item for item in result_dirs if (item / "textured_mesh.glb").is_file()]
    candidates = textured_dirs or result_dirs
    if not candidates:
        raise RuntimeError("没有找到可恢复的本地生成结果。")
    source_dir = max(candidates, key=lambda item: item.stat().st_mtime)
    job = create_job("generation")
    shape_path = copy_result_file(source_dir / "white_mesh.glb", job["id"], "shape_mesh.glb")
    textured_source = source_dir / "textured_mesh.glb"
    textured_path = copy_result_file(textured_source, job["id"], "textured_mesh.glb") if textured_source.is_file() else None
    viewer_name = "textured_mesh.html" if (source_dir / "textured_mesh.html").is_file() else "white_mesh.html"
    viewer_url = f"{BACKEND_URL.rstrip('/')}/static/{source_dir.name}/{viewer_name}"
    viewer_html = (
        '<div class="recovered-viewer">'
        f'<iframe src="{viewer_url}" height="690" width="100%" frameborder="0"></iframe>'
        "</div>"
    )
    result = {
        "mode": "textured" if textured_path else "shape",
        "viewer_html": viewer_html,
        "stats": {},
        "seed": None,
        "view_count": None,
        "has_shape": bool(shape_path),
        "has_textured": bool(textured_path),
        "shape_download": f"/api/jobs/{job['id']}/download/shape" if shape_path else None,
        "textured_download": f"/api/jobs/{job['id']}/download/textured" if textured_path else None,
        "recovered": True,
    }
    update_job(
        job["id"],
        status="succeeded",
        status_text="已恢复最近一次本地生成结果",
        result=result,
        _shape_path=shape_path,
        _textured_path=textured_path,
    )
    with JOBS_LOCK:
        return public_job(dict(JOBS[job["id"]]))


def rewrite_viewer_html(html: str | None) -> str:
    if not html:
        return ""
    base = BACKEND_URL.rstrip("/")
    rewritten = str(html).replace('src="/static/', f'src="{base}/static/')
    rewritten = rewritten.replace("src='/static/", f"src='{base}/static/")
    return rewritten


def get_client():
    try:
        from gradio_client import Client
    except ImportError as error:
        raise RuntimeError("缺少 gradio_client；请使用混元本地环境中的 Python 启动本页面。") from error
    return Client(BACKEND_URL, verbose=False)


def get_handle_file():
    try:
        from gradio_client import handle_file
    except ImportError as error:
        raise RuntimeError("缺少 gradio_client.handle_file。") from error
    return handle_file


def run_generation(job_id: str, image_paths: dict[str, str], params: dict) -> None:
    mode = "textured" if params.get("mode") == "textured" else "shape"
    update_job(job_id, status="running", status_text="正在调用本地混元模型")
    try:
        health = backend_health()
        if not health.get("online"):
            raise RuntimeError(health.get("message") or "本地多视图服务未连接，请先启动 8081 服务。")

        steps = safe_number(params.get("steps"), 30, 1, 100, integer=True)
        guidance = safe_number(params.get("guidance_scale"), 5.0, 1, 30)
        seed = safe_number(params.get("seed"), 1234, 0, 10_000_000, integer=True)
        octree = safe_number(params.get("octree_resolution"), 256, 16, 512, integer=True)
        chunks = safe_number(params.get("num_chunks"), 8000, 1000, 5_000_000, integer=True)
        remove_background = bool(params.get("remove_background", True))
        randomize_seed = bool(params.get("randomize_seed", True))

        update_job(job_id, status_text="模型正在生成三维形体")
        client = get_client()
        handle_file = get_handle_file()
        api_name = "/generation_all" if mode == "textured" else "/shape_generation"
        view_inputs = [
            handle_file(image_paths[view]) if image_paths.get(view) else None
            for view in VIEW_KEYS
        ]
        with CLIENT_CALL_LOCK:
            output = client.predict(
                None,
                *view_inputs,
                steps,
                guidance,
                seed,
                octree,
                remove_background,
                chunks,
                randomize_seed,
                api_name=api_name,
            )

        if mode == "textured":
            shape_source, textured_source, viewer_html, stats, resolved_seed = output
            textured_path = copy_result_file(textured_source, job_id, "textured_mesh.glb")
        else:
            shape_source, viewer_html, stats, resolved_seed = output
            textured_path = None
        shape_path = copy_result_file(shape_source, job_id, "shape_mesh.glb")
        result = {
            "mode": mode,
            "viewer_html": rewrite_viewer_html(viewer_html),
            "stats": json_safe(stats),
            "seed": resolved_seed,
            "view_count": sum(1 for view in VIEW_KEYS if image_paths.get(view)),
            "has_shape": bool(shape_path),
            "has_textured": bool(textured_path),
            "shape_download": f"/api/jobs/{job_id}/download/shape" if shape_path else None,
            "textured_download": f"/api/jobs/{job_id}/download/textured" if textured_path else None,
        }
        update_job(
            job_id,
            status="succeeded",
            status_text="三维资产草稿已生成",
            result=result,
            _shape_path=shape_path,
            _textured_path=textured_path,
        )
    except Exception as error:  # Local model errors must be surfaced to the page.
        update_job(job_id, status="failed", status_text="生成失败", error=str(error))


def run_export(job_id: str, source_job_id: str, options: dict) -> None:
    update_job(job_id, status="running", status_text="正在转换导出文件")
    try:
        with JOBS_LOCK:
            source_job = dict(JOBS.get(source_job_id) or {})
        if source_job.get("status") != "succeeded":
            raise RuntimeError("请先完成一次三维生成。")
        shape_path = source_job.get("_shape_path")
        textured_path = source_job.get("_textured_path")
        if not shape_path:
            raise RuntimeError("生成结果中缺少形体文件。")

        file_type = str(options.get("file_type", "glb")).lower()
        if file_type not in ALLOWED_EXPORT_TYPES:
            file_type = "glb"
        simplify = bool(options.get("simplify", False))
        include_texture = bool(options.get("include_texture", False))
        if include_texture and not textured_path:
            raise RuntimeError("当前结果没有材质模型，不能勾选包含材质。")
        target_faces = safe_number(options.get("target_faces"), 10000, 100, 1_000_000, integer=True)

        client = get_client()
        handle_file = get_handle_file()
        with CLIENT_CALL_LOCK:
            viewer_html, exported_source = client.predict(
                handle_file(shape_path),
                handle_file(textured_path) if textured_path else None,
                file_type,
                simplify,
                include_texture,
                target_faces,
                api_name="/on_export_click",
            )
        export_path = copy_result_file(exported_source, job_id, f"reverse_model.{file_type}")
        if not export_path:
            raise RuntimeError("导出服务没有返回文件。")
        result = {
            "viewer_html": rewrite_viewer_html(viewer_html),
            "file_type": file_type,
            "include_texture": include_texture,
            "download": f"/api/jobs/{job_id}/download/export",
        }
        update_job(
            job_id,
            status="succeeded",
            status_text="导出文件已准备好",
            result=result,
            _export_path=export_path,
        )
    except Exception as error:
        update_job(job_id, status="failed", status_text="导出失败", error=str(error))


def save_uploaded_image(field) -> str:
    filename = Path(field.filename or "upload.png").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise ValueError("仅支持 PNG、JPG、JPEG 或 WebP 图片。")
    upload_id = uuid.uuid4().hex
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_ROOT / f"{upload_id}{suffix}"
    written = 0
    with target.open("wb") as output:
        while True:
            chunk = field.file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                output.close()
                target.unlink(missing_ok=True)
                raise ValueError("图片不能超过 25 MB。")
            output.write(chunk)
    if written == 0:
        target.unlink(missing_ok=True)
        raise ValueError("上传图片为空。")
    try:
        from PIL import Image

        with Image.open(target) as image:
            image.verify()
    except Exception as error:
        target.unlink(missing_ok=True)
        raise ValueError("无法识别这张图片。") from error
    return str(target)


class BetaHandler(SimpleHTTPRequestHandler):
    server_version = "OntoTwinReverseModelingBeta/0.2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_ROOT), **kwargs)

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 1024 * 1024:
            raise ValueError("请求内容过大。")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/health":
            return self.send_json(backend_health())
        if path == "/api/examples":
            files = []
            if EXAMPLE_ROOT.is_dir():
                for item in sorted(EXAMPLE_ROOT.glob("*.png"))[:12]:
                    files.append({"name": item.name, "url": f"/api/examples/{item.name}"})
            return self.send_json({"items": files})
        if path.startswith("/api/examples/"):
            name = path.split("/")[-1]
            target = EXAMPLE_ROOT / name
            if Path(name).name != name or target.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES or not target.is_file():
                return self.send_error(HTTPStatus.NOT_FOUND)
            return self.send_file(target, inline=True)
        if path.startswith("/api/jobs/"):
            parts = [part for part in path.split("/") if part]
            if len(parts) == 3:
                job_id = parts[2]
                with JOBS_LOCK:
                    job = dict(JOBS.get(job_id) or {})
                if not job:
                    return self.send_json({"error": "任务不存在"}, HTTPStatus.NOT_FOUND)
                return self.send_json(public_job(job))
            if len(parts) == 5 and parts[3] == "download":
                job_id, kind = parts[2], parts[4]
                with JOBS_LOCK:
                    job = dict(JOBS.get(job_id) or {})
                key_map = {"shape": "_shape_path", "textured": "_textured_path", "export": "_export_path"}
                target_value = job.get(key_map.get(kind, ""))
                target = Path(target_value) if target_value else None
                if not target or not target.is_file():
                    return self.send_error(HTTPStatus.NOT_FOUND)
                return self.send_file(target, inline=False)
        return super().do_GET()

    def send_file(self, path: Path, inline=False):
        size = path.stat().st_size
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        disposition = "inline" if inline else "attachment"
        self.send_header("Content-Disposition", f'{disposition}; filename="{path.name}"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with path.open("rb") as source:
            shutil.copyfileobj(source, self.wfile)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/generate":
                content_type = self.headers.get("Content-Type", "")
                if "multipart/form-data" not in content_type:
                    return self.send_json({"error": "需要上传多视图参考图片"}, HTTPStatus.BAD_REQUEST)
                content_length = int(self.headers.get("Content-Length", "0") or "0")
                if content_length > MAX_MULTIVIEW_REQUEST_BYTES:
                    return self.send_json({"error": "上传内容过大"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
                )
                params_raw = form.getfirst("params", "{}")
                params = json.loads(params_raw)
                image_paths = {}
                for view in VIEW_KEYS:
                    field_name = f"{view}_image"
                    field = form[field_name] if field_name in form else None
                    if isinstance(field, list):
                        field = field[0] if field else None
                    if field is not None and getattr(field, "file", None):
                        image_paths[view] = save_uploaded_image(field)
                if not image_paths.get("front"):
                    return self.send_json({"error": "请至少上传正面视图"}, HTTPStatus.BAD_REQUEST)
                job = create_job("generation")
                threading.Thread(target=run_generation, args=(job["id"], image_paths, params), daemon=True).start()
                return self.send_json(public_job(job), HTTPStatus.ACCEPTED)

            if parsed.path == "/api/recover-latest":
                return self.send_json(recover_latest_result())

            if parsed.path == "/api/export":
                payload = self.read_json()
                source_job_id = str(payload.get("source_job_id") or "")
                with JOBS_LOCK:
                    source_exists = source_job_id in JOBS
                if not source_exists:
                    return self.send_json({"error": "生成任务不存在"}, HTTPStatus.NOT_FOUND)
                job = create_job("export", source_job_id)
                threading.Thread(target=run_export, args=(job["id"], source_job_id, payload), daemon=True).start()
                return self.send_json(public_job(job), HTTPStatus.ACCEPTED)
        except (ValueError, json.JSONDecodeError) as error:
            return self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            return self.send_json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
        return self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args))


def main():
    global BACKEND_URL
    parser = argparse.ArgumentParser(description="OntoTwin 逆向建模 Beta 前端")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8766, type=int)
    parser.add_argument("--backend", default=os.environ.get("HUNYUAN_BACKEND", DEFAULT_BACKEND))
    args = parser.parse_args()
    BACKEND_URL = args.backend.rstrip("/")
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), BetaHandler)
    print("OntoTwin 逆向建模 Beta 已启动")
    print(f"页面地址: http://{args.host}:{args.port}")
    print(f"混元服务: {BACKEND_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeta 服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
