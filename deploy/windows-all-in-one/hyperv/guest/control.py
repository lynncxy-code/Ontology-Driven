#!/usr/bin/env python3
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


RELEASE_ROOT = pathlib.Path("/opt/ontotwin/release")
DEPLOY_ROOT = RELEASE_ROOT / "Deploy"
DATA_ROOT = pathlib.Path("/var/lib/ontotwin")
TOKEN = pathlib.Path("/etc/ontotwin/control.token").read_text(encoding="utf-8").strip()
BOOTSTRAP_LOG = DATA_ROOT / "bootstrap-last.log"
BOOTSTRAP_IN_PROGRESS = DATA_ROOT / "bootstrap.in-progress"


def compose(*arguments, check=True, capture_output=False, timeout=None):
    command = [
        "/usr/local/bin/docker", "compose",
        "--env-file", str(DEPLOY_ROOT / ".env"),
        "-f", str(DEPLOY_ROOT / "docker-compose.release.yml"),
        *arguments,
    ]
    return subprocess.run(
        command,
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


def compose_status():
    docker = pathlib.Path("/usr/local/bin/docker")
    environment = DEPLOY_ROOT / ".env"
    compose_file = DEPLOY_ROOT / "docker-compose.release.yml"
    missing = [
        str(path) for path in (docker, environment, compose_file)
        if not path.is_file()
    ]
    if missing:
        return None, "", "Bootstrap is still preparing: missing " + ", ".join(missing)
    try:
        result = compose("ps", "--format", "json", check=False, capture_output=True, timeout=15)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return None, "", "Docker Compose status timed out after 15 seconds."
    except Exception as error:
        return None, "", f"Docker Compose status unavailable: {error}"


def read_env():
    result = {}
    for line in (DEPLOY_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def backend_ready():
    try:
        urllib.request.urlopen("http://127.0.0.1:5000/", timeout=3).read(1)
        return True
    except Exception:
        return False


def bootstrap_log_tail(max_bytes=16 * 1024):
    try:
        with BOOTSTRAP_LOG.open("rb") as source:
            source.seek(0, os.SEEK_END)
            size = source.tell()
            source.seek(max(0, size - max_bytes), os.SEEK_SET)
            return source.read().decode("utf-8", errors="replace")
    except Exception as error:
        return f"Bootstrap log unavailable: {error}"


def bootstrap_in_progress():
    if BOOTSTRAP_IN_PROGRESS.exists():
        return True
    try:
        result = subprocess.run(
            ["/usr/bin/systemctl", "show", "--property=ActiveState", "--value",
             "ontotwin-bootstrap.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() in {"activating", "active", "reloading"}
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "OntoTwinGuestControl/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def authorized(self):
        if self.headers.get("X-OntoTwin-Token", "") == TOKEN:
            return True
        self.send_error(403)
        return False

    def write_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.authorized():
            return
        if self.path != "/status":
            self.send_error(404)
            return
        compose_exit_code, services, compose_error = compose_status()
        bootstrap_active = bootstrap_in_progress()
        self.write_json(200, {
            "ready": not bootstrap_active and backend_ready(),
            "bootstrap_in_progress": bootstrap_active,
            "compose_exit_code": compose_exit_code,
            "services": services,
            "compose_error": compose_error,
            "bootstrap_log_tail": bootstrap_log_tail(),
        })

    def do_POST(self):
        if not self.authorized():
            return
        if self.path == "/shutdown":
            self.write_json(200, {"accepted": True})
            threading.Thread(
                target=lambda: subprocess.run(["/usr/sbin/shutdown", "-h", "now"], check=False),
                daemon=True,
            ).start()
            return
        if self.path == "/backup":
            self.make_backup()
            return
        if self.path == "/stack/start":
            try:
                result = compose("up", "-d", "backend", check=False, capture_output=True, timeout=600)
                self.write_json(200 if result.returncode == 0 else 500, {
                    "exit_code": result.returncode,
                    "output": result.stdout + result.stderr,
                })
            except Exception as error:
                self.write_json(503, {"exit_code": None, "output": str(error)})
            return
        if self.path == "/stack/stop":
            try:
                result = compose("stop", check=False, capture_output=True, timeout=180)
                self.write_json(200 if result.returncode == 0 else 500, {
                    "exit_code": result.returncode,
                    "output": result.stdout + result.stderr,
                })
            except Exception as error:
                self.write_json(503, {"exit_code": None, "output": str(error)})
            return
        self.send_error(404)

    def make_backup(self):
        environment = read_env()
        backup_root = DATA_ROOT / "backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        working = pathlib.Path(tempfile.mkdtemp(prefix=f"zhhz-{stamp}-", dir=backup_root))
        archive = backup_root / f"OntoTwin-ZHHZ-{stamp}.tar.gz"
        try:
            database_path = working / "postgres.dump"
            container = compose("ps", "-q", "db", capture_output=True).stdout.strip()
            if not container:
                raise RuntimeError("PostgreSQL container is not running")
            with database_path.open("wb") as output:
                result = subprocess.run([
                    "/usr/local/bin/docker", "exec", "-i", container,
                    "pg_dump", "-U", environment["POSTGRES_USER"],
                    "-d", environment["POSTGRES_DB"], "-Fc",
                ], stdout=output, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))

            manifest = {
                "product": "OntoTwin ZHHZ",
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "release_version": environment.get("ONTOTWIN_RELEASE_VERSION", "unknown"),
                "data_version": environment.get("ONTOTWIN_DATA_VERSION", "unknown"),
                "project_id": "ds_1784694647848",
                "neo4j_policy": "rebuild-from-release-seed",
            }
            (working / "backup-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            assets = DATA_ROOT / "release-data" / "project_assets"
            with tarfile.open(archive, "w:gz") as bundle:
                bundle.add(database_path, arcname="postgres.dump")
                bundle.add(working / "backup-manifest.json", arcname="backup-manifest.json")
                if assets.exists():
                    bundle.add(assets, arcname="project_assets")

            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Length", str(archive.stat().st_size))
            self.send_header("Content-Disposition", f'attachment; filename="{archive.name}"')
            self.end_headers()
            with archive.open("rb") as source:
                shutil.copyfileobj(source, self.wfile, length=1024 * 1024)
        except Exception as error:
            self.write_json(500, {"error": str(error)})
        finally:
            shutil.rmtree(working, ignore_errors=True)
            # The host keeps the customer-facing backup. Avoid retaining a
            # second full copy on the limited guest data disk after streaming.
            archive.unlink(missing_ok=True)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", 49274), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
