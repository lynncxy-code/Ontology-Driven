#!/bin/bash
set -Eeuo pipefail

HOST_URL="http://172.28.251.1:48075"
RELEASE_ROOT="/opt/ontotwin/release"
DATA_ROOT="/var/lib/ontotwin"
WORK_ROOT="$DATA_ROOT/bootstrap"
TOKEN_FILE="/etc/ontotwin/control.token"
PAYLOAD_MARKER="$DATA_ROOT/bootstrap-payload.sha256"
IMAGES_MARKER="$DATA_ROOT/bootstrap-images.sha256"
BOOTSTRAP_LOG="$DATA_ROOT/bootstrap-last.log"
BOOTSTRAP_IN_PROGRESS="$DATA_ROOT/bootstrap.in-progress"

log() {
  printf '[%s] %s\n' "$(date --iso-8601=seconds)" "$*"
  python3 - "$HOST_URL/bootstrap/progress" "$*" <<'PY' || true
import sys
import urllib.request
request = urllib.request.Request(sys.argv[1], data=sys.argv[2].encode("utf-8"), method="POST")
urllib.request.urlopen(request, timeout=5).read()
PY
}

download() {
  local remote="$1"
  local output="$2"
  python3 - "$remote" "$output" <<'PY'
import sys
import urllib.request
urllib.request.urlretrieve(sys.argv[1], sys.argv[2])
PY
}

install_control_service() {
  install -m 0755 "$WORK_ROOT/control.py" /usr/local/sbin/ontotwin-control.py
  cat >/etc/systemd/system/ontotwin-control.service <<'EOF'
[Unit]
Description=OntoTwin ZHHZ guest control service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /usr/local/sbin/ontotwin-control.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable ontotwin-control.service
  systemctl restart ontotwin-control.service
}

ensure_root_filesystem_capacity() {
  local root_source root_type root_device root_device_name root_device_type root_sysfs_path
  local partition_file parent_name parent_type part_number grow_output
  local root_size_bytes root_available_bytes

  root_source="$(findmnt -nro SOURCE -e /)"
  root_type="$(findmnt -nro FSTYPE -e /)"
  root_size_bytes="$(df -B1 --output=size / | tail -n 1 | tr -d '[:space:]')"

  # The distributed Ubuntu image is intentionally compact. The Windows host
  # expands its dynamic VHDX before first boot; grow the root partition and
  # filesystem here as an idempotent fallback if cloud-init has not done so.
  # Only inspect direct block partitions while the root filesystem is still
  # below the release contract. Reading the partition number from sysfs avoids
  # lsblk's padded numeric output (for example "    1"), which growpart rejects.
  if [ "$root_size_bytes" -lt 17179869184 ]; then
    root_device="$(readlink -f -- "$root_source" 2>/dev/null || printf '%s\n' "$root_source")"
    root_device_name="${root_device##*/}"
    root_device_type="$(lsblk -dnro TYPE -- "$root_device" 2>/dev/null | awk 'NF {print $1; exit}')"
    root_sysfs_path="$(readlink -f -- "/sys/class/block/$root_device_name" 2>/dev/null || true)"
    partition_file="/sys/class/block/$root_device_name/partition"
    parent_name=""
    parent_type=""
    part_number=""
    if [ -n "$root_sysfs_path" ] && [ -r "$partition_file" ]; then
      parent_name="$(basename "$(dirname "$root_sysfs_path")")"
      parent_type="$(lsblk -dnro TYPE -- "/dev/$parent_name" 2>/dev/null | awk 'NF {print $1; exit}')"
      part_number="$(awk 'NF {print $1; exit}' "$partition_file")"
    fi
    log "Root partition inspection: source=$root_source resolved=$root_device type=${root_device_type:-unknown} parent=${parent_name:-unknown} parent_type=${parent_type:-unknown} partition=${part_number:-unknown}"

    if [[ "$part_number" =~ ^[0-9]+$ ]] \
      && [ "$part_number" -gt 0 ] \
      && [ "$root_device_type" = "part" ] \
      && [ -n "$parent_name" ] \
      && [ "$parent_name" != "$root_device_name" ] \
      && [ "$parent_type" = "disk" ] \
      && [ -b "/dev/$parent_name" ] \
      && command -v growpart >/dev/null 2>&1; then
      grow_output=""
      if ! grow_output="$(growpart "/dev/$parent_name" "$part_number" 2>&1)"; then
        if ! printf '%s\n' "$grow_output" | grep -qi 'NOCHANGE'; then
          # The final capacity checks below remain authoritative. A transient
          # growpart failure must not abort a VM whose partition was already
          # expanded by cloud-init between the initial probe and this fallback.
          log "Root partition expansion warning: $grow_output"
        fi
      fi
      [ -z "$grow_output" ] || log "Root partition check: $grow_output"
      udevadm settle 2>/dev/null || true
    else
      log "Root partition expansion was not attempted because a direct numeric partition could not be identified safely"
    fi
  else
    log "Root partition expansion is not required; the root filesystem already meets the 16 GiB contract"
  fi

  case "$root_type" in
    ext2|ext3|ext4)
      resize2fs "$root_source"
      ;;
    xfs)
      xfs_growfs /
      ;;
    btrfs)
      btrfs filesystem resize max /
      ;;
    *)
      log "Root filesystem type '$root_type' is not explicitly resizable; validating its current capacity"
      ;;
  esac

  root_size_bytes="$(df -B1 --output=size / | tail -n 1 | tr -d '[:space:]')"
  root_available_bytes="$(df -B1 --output=avail / | tail -n 1 | tr -d '[:space:]')"
  if [ "$root_available_bytes" -lt 8589934592 ]; then
    # Only disposable operating-system caches are removed. OntoTwin payloads,
    # databases, images and customer settings live on the separate data disk.
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/*
    journalctl --vacuum-size=64M >/dev/null 2>&1 || true
    root_available_bytes="$(df -B1 --output=avail / | tail -n 1 | tr -d '[:space:]')"
  fi
  log "Root filesystem capacity: total=$root_size_bytes bytes available=$root_available_bytes bytes"
  if [ "$root_size_bytes" -lt 17179869184 ]; then
    log "Bootstrap failed: the appliance root filesystem is smaller than 16 GiB; the Windows host must refresh and expand the system VHDX"
    exit 1
  fi
  if [ "$root_available_bytes" -lt 8589934592 ]; then
    log "Bootstrap failed: less than 8 GiB is available on the appliance root filesystem"
    exit 1
  fi
}

mkdir -p /etc/ontotwin "$DATA_ROOT"
download "$HOST_URL/bootstrap/token" "$TOKEN_FILE"
chmod 0600 "$TOKEN_FILE"

data_device=""
for candidate in /dev/sdb /dev/sdc /dev/sdd; do
  if [ -b "$candidate" ]; then
    data_device="$candidate"
    break
  fi
done
if [ -z "$data_device" ]; then
  log "No OntoTwin data disk was detected"
  exit 1
fi
if ! blkid "$data_device" >/dev/null 2>&1; then
  log "Formatting OntoTwin data disk"
  mkfs.ext4 -F -L ONTOTWIN_DATA "$data_device"
fi
if ! grep -q '^LABEL=ONTOTWIN_DATA ' /etc/fstab; then
  printf 'LABEL=ONTOTWIN_DATA /var/lib/ontotwin ext4 defaults,nofail 0 2\n' >> /etc/fstab
fi
mountpoint -q "$DATA_ROOT" || mount "$DATA_ROOT"
mkdir -p "$WORK_ROOT" "$DATA_ROOT/docker" "$DATA_ROOT/release-data/project_assets" "$DATA_ROOT/release-data/exports" "$DATA_ROOT/backups"

# A failed previous bootstrap leaves this marker behind. Capture that state
# before recording the current attempt so an RC upgrade can replace a
# half-initialized PostgreSQL/Neo4j Docker baseline as well as a healthy one.
previous_bootstrap_incomplete=false
if [ -f "$BOOTSTRAP_IN_PROGRESS" ]; then
  previous_bootstrap_incomplete=true
fi

if [ -f "$BOOTSTRAP_LOG" ] && [ "$(stat -c %s "$BOOTSTRAP_LOG" 2>/dev/null || printf 0)" -gt 2097152 ]; then
  mv -f "$BOOTSTRAP_LOG" "$BOOTSTRAP_LOG.previous"
fi
touch "$BOOTSTRAP_LOG"
chmod 0600 "$BOOTSTRAP_LOG"
exec > >(tee -a "$BOOTSTRAP_LOG") 2>&1
printf '%s\n' "$(date --iso-8601=seconds)" > "$BOOTSTRAP_IN_PROGRESS"
chmod 0600 "$BOOTSTRAP_IN_PROGRESS"

bootstrap_error() {
  local exit_code="$?"
  local line_number="$1"
  local failed_command="$2"
  trap - ERR
  log "Bootstrap failed: exit=$exit_code line=$line_number command=$failed_command"
  exit "$exit_code"
}
trap 'bootstrap_error "$LINENO" "$BASH_COMMAND"' ERR
printf '\n[%s] Bootstrap attempt started\n' "$(date --iso-8601=seconds)"

log "Downloading and verifying the embedded backend payload"
download "$HOST_URL/payload/SHA256SUMS" "$WORK_ROOT/SHA256SUMS"
control_checksums="$(awk '$2=="control.py" {print $1}' "$WORK_ROOT/SHA256SUMS")"
if [ "$(printf '%s\n' "$control_checksums" | sed '/^$/d' | wc -l)" -ne 1 ] \
  || ! printf '%s' "$control_checksums" | grep -Eq '^[0-9a-fA-F]{64}$'; then
  log "Bootstrap failed: payload checksums do not identify exactly one control.py"
  exit 1
fi
if [ ! -f "$WORK_ROOT/control.py" ] \
  || ! printf '%s  %s\n' "$control_checksums" "$WORK_ROOT/control.py" | sha256sum -c - >/dev/null 2>&1; then
  log "Downloading the early diagnostic control service"
  download "$HOST_URL/payload/control.py" "$WORK_ROOT/control.py"
fi
printf '%s  %s\n' "$control_checksums" "$WORK_ROOT/control.py" | sha256sum -c - >/dev/null
install_control_service
log "Early diagnostic control service started"
ensure_root_filesystem_capacity

payload_fingerprint="$(sha256sum "$WORK_ROOT/SHA256SUMS" | awk '{print $1}')"
image_checksum_count="$(awk '$2=="backend-image.tar" || $2=="postgres-image.tar" || $2=="neo4j-image.tar" {count++} END {print count+0}' "$WORK_ROOT/SHA256SUMS")"
if [ "$image_checksum_count" -ne 3 ]; then
  log "Bootstrap failed: payload checksums do not identify exactly three container archives"
  exit 1
fi
image_fingerprint="$({
  awk '$2=="backend-image.tar" || $2=="postgres-image.tar" || $2=="neo4j-image.tar" {print}' "$WORK_ROOT/SHA256SUMS" |
    sort
} | sha256sum | awk '{print $1}')"
installed_fingerprint="$(cat "$PAYLOAD_MARKER" 2>/dev/null || true)"

# On ordinary starts the payload is unchanged. Avoid repeatedly extracting the
# release and loading several large Docker archives, but only when both the
# system-disk installation and data-disk images are demonstrably complete.
system_payload_complete=false
if [ "$installed_fingerprint" = "$payload_fingerprint" ] \
  && [ -x /usr/local/bin/docker ] \
  && [ -x /usr/local/lib/docker/cli-plugins/docker-compose ] \
  && [ -f /usr/local/sbin/ontotwin-control.py ] \
  && [ -f /etc/systemd/system/docker.service ] \
  && [ -f /etc/systemd/system/ontotwin-control.service ] \
  && [ -f /etc/systemd/system/ontotwin-stack.service ] \
  && [ -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" ] \
  && [ -f "$RELEASE_ROOT/Deploy/.env" ]; then
  systemctl daemon-reload
  systemctl enable --now docker.service
  system_payload_complete=true
  image_count=0
  while IFS='=' read -r key image; do
    case "$key" in
      BACKEND_IMAGE|POSTGRES_IMAGE|NEO4J_IMAGE)
        image="${image%$'\r'}"
        image_count=$((image_count + 1))
        if [ -z "$image" ] || ! docker image inspect "$image" >/dev/null 2>&1; then
          system_payload_complete=false
        fi
        ;;
    esac
  done < "$RELEASE_ROOT/Deploy/.env"
  if [ "$image_count" -ne 3 ]; then
    system_payload_complete=false
  fi
fi

if [ "$system_payload_complete" = true ]; then
  log "Embedded backend payload is unchanged; starting the installed services"
  systemctl enable ontotwin-control.service ontotwin-stack.service
  systemctl restart ontotwin-control.service
  systemctl start --no-block ontotwin-stack.service
  rm -f "$BOOTSTRAP_IN_PROGRESS"
  exit 0
fi

while read -r checksum filename; do
  filename="${filename%$'\r'}"
  [ -n "$filename" ] || continue
  target="$WORK_ROOT/$filename"
  if [ ! -f "$target" ] || ! printf '%s  %s\n' "$checksum" "$target" | sha256sum -c - >/dev/null 2>&1; then
    log "Downloading $filename"
    download "$HOST_URL/payload/$filename" "$target"
  fi
  printf '%s  %s\n' "$checksum" "$target" | sha256sum -c - >/dev/null
done < "$WORK_ROOT/SHA256SUMS"
log "Embedded backend payload verified"

log "Installing the embedded Docker Engine"
tar -xzf "$WORK_ROOT/docker-static.tgz" -C /usr/local/bin --strip-components=1
install -D -m 0755 "$WORK_ROOT/docker-compose" /usr/local/lib/docker/cli-plugins/docker-compose
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<EOF
{
  "data-root": "$DATA_ROOT/docker",
  "log-driver": "local",
  "log-opts": { "max-size": "20m", "max-file": "5" }
}
EOF
cat >/etc/systemd/system/docker.service <<'EOF'
[Unit]
Description=OntoTwin embedded Docker Engine
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/local/bin/dockerd --host=unix:///var/run/docker.sock
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStartSec=0
Restart=always
RestartSec=2
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
EOF
cat >/etc/systemd/system/docker.socket <<'EOF'
[Unit]
Description=Docker Socket for the API

[Socket]
ListenStream=/var/run/docker.sock
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF
systemctl daemon-reload
systemctl enable --now docker.service
log "Embedded Docker Engine started"

# docker's restart policy can bring the previous containers up before this
# bootstrap runs. Stop its systemd unit first, then remove the old containers
# and network before replacing release files or images. `down` intentionally
# omits --volumes so PostgreSQL, Neo4j and release-state data survive upgrades.
systemctl stop ontotwin-stack.service 2>/dev/null || true
if [ -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" ] && [ -f "$RELEASE_ROOT/Deploy/.env" ]; then
  log "Removing the previous OntoTwin containers and network before payload upgrade"
  if ! teardown_output="$(docker compose --env-file "$RELEASE_ROOT/Deploy/.env" \
    -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" \
    down --remove-orphans --timeout 120 2>&1)"; then
    printf '%s\n' "$teardown_output"
    teardown_summary="$(printf '%s\n' "$teardown_output" | tail -n 8 | tr '\n' ' ')"
    log "Compose teardown did not complete; continuing with project-label cleanup: $teardown_summary"
    docker ps --all --filter label=com.docker.compose.project=ontotwin-zhhz || true
    docker network ls --filter label=com.docker.compose.project=ontotwin-zhhz || true
  else
    printf '%s\n' "$teardown_output"
  fi
fi

# An appliance upgrade replaces the guest system disk, so the old Compose
# files can be gone even though Docker's data-root (and its restart-policy
# containers) survives on the separate data disk. Remove only objects bearing
# this product's Compose project label. Named volumes are deliberately neither
# selected nor removed.
residual_container_output="$(
  docker ps --all --quiet --filter label=com.docker.compose.project=ontotwin-zhhz
)"
residual_containers=()
if [ -n "$residual_container_output" ]; then
  mapfile -t residual_containers <<< "$residual_container_output"
fi
if [ "${#residual_containers[@]}" -gt 0 ]; then
  log "Stopping residual OntoTwin containers from the persistent data disk"
  docker stop --time 120 "${residual_containers[@]}"
  docker rm "${residual_containers[@]}"
fi
residual_network_output="$(
  docker network ls --quiet --filter label=com.docker.compose.project=ontotwin-zhhz
)"
residual_networks=()
if [ -n "$residual_network_output" ]; then
  mapfile -t residual_networks <<< "$residual_network_output"
fi
if [ "${#residual_networks[@]}" -gt 0 ]; then
  log "Removing residual OntoTwin Docker networks"
  docker network rm "${residual_networks[@]}"
fi
# Keep an existing control service alive so the host can read bootstrap
# diagnostics while large images are being upgraded. It is restarted after the
# new control.py and release environment are in place.

log "Installing OntoTwin release files"
rm -rf /opt/ontotwin/release.new
mkdir -p /opt/ontotwin/release.new
tar -xzf "$WORK_ROOT/release.tar.gz" -C /opt/ontotwin/release.new
rm -rf /opt/ontotwin/release.previous
if [ -d "$RELEASE_ROOT" ]; then
  mv "$RELEASE_ROOT" /opt/ontotwin/release.previous
fi
mv /opt/ontotwin/release.new "$RELEASE_ROOT"

# Pre-customer RC packages may explicitly request a clean packaged baseline.
# Preserve the former Docker state and release data by moving them to a
# timestamped directory on the same data disk, then initialize fresh paths.
# The persistent release.env (passwords and customer integrations) and normal
# user backups are deliberately retained outside this baseline snapshot.
reset_backend_baseline="$(python3 - "$RELEASE_ROOT/release-manifest.json" <<'PY'
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print("true" if manifest.get("reset_backend_baseline_on_upgrade") is True else "false")
PY
)"
if [ "$reset_backend_baseline" = true ] \
  && { [ -n "$installed_fingerprint" ] || [ "$previous_bootstrap_incomplete" = true ]; }; then
  baseline_backup_root="$DATA_ROOT/baseline-backups/$(date -u +%Y%m%d-%H%M%S)-${payload_fingerprint:0:12}"
  if [ -e "$baseline_backup_root" ]; then
    log "Bootstrap failed: the baseline backup destination already exists: $baseline_backup_root"
    exit 1
  fi
  log "Backing up the previous backend baseline before applying the packaged ZHHZ data"
  systemctl stop docker.service
  mkdir -p "$baseline_backup_root"
  if [ -d "$DATA_ROOT/docker" ]; then
    mv "$DATA_ROOT/docker" "$baseline_backup_root/docker"
  fi
  if [ -d "$DATA_ROOT/release-data" ]; then
    mv "$DATA_ROOT/release-data" "$baseline_backup_root/release-data"
  fi
  mkdir -p "$DATA_ROOT/docker" "$DATA_ROOT/release-data/project_assets" "$DATA_ROOT/release-data/exports"
  rm -f "$PAYLOAD_MARKER" "$IMAGES_MARKER"
  systemctl start docker.service
  log "Previous backend baseline saved at $baseline_backup_root"
fi
if [ -d "$RELEASE_ROOT/Data" ]; then
  cp -a -n "$RELEASE_ROOT/Data/." "$DATA_ROOT/release-data/"
fi
rm -rf "$RELEASE_ROOT/Data"
ln -s "$DATA_ROOT/release-data" "$RELEASE_ROOT/Data"

env_template="$RELEASE_ROOT/Deploy/customer.env.example"
mapfile -t required_images < <(
  awk -F= '$1=="BACKEND_IMAGE" || $1=="POSTGRES_IMAGE" || $1=="NEO4J_IMAGE" { sub(/\r$/, "", $2); print $2 }' \
    "$env_template"
)
if [ "${#required_images[@]}" -ne 3 ]; then
  log "Bootstrap failed: the release environment does not declare exactly three container images"
  exit 1
fi

images_ready=false
if [ "$(cat "$IMAGES_MARKER" 2>/dev/null || true)" = "$image_fingerprint" ]; then
  images_ready=true
  for image in "${required_images[@]}"; do
    if ! docker image inspect "$image" >/dev/null 2>&1; then
      images_ready=false
    fi
  done
fi

if [ "$images_ready" = true ]; then
  log "Embedded container images are already loaded"
else
  for image_archive in backend-image.tar postgres-image.tar neo4j-image.tar; do
    log "Loading $image_archive"
    docker load --input "$WORK_ROOT/$image_archive"
  done
  for image in "${required_images[@]}"; do
    if ! docker image inspect "$image" >/dev/null 2>&1; then
      log "Bootstrap failed: required image was not provided by the payload: $image"
      docker image ls --format '{{.Repository}}:{{.Tag}}' || true
      exit 1
    fi
  done
  printf '%s\n' "$image_fingerprint" > "$IMAGES_MARKER.new"
  chmod 0600 "$IMAGES_MARKER.new"
  mv -f "$IMAGES_MARKER.new" "$IMAGES_MARKER"
fi

env_file="$RELEASE_ROOT/Deploy/.env"
persistent_env="$DATA_ROOT/release.env"
log "Merging the release environment while preserving customer secrets and integrations"
python3 - "$env_template" "$persistent_env" <<'PY'
import os
import pathlib
import secrets
import sys

template_path = pathlib.Path(sys.argv[1])
environment_path = pathlib.Path(sys.argv[2])
template_lines = template_path.read_text(encoding="utf-8").splitlines()
old_lines = environment_path.read_text(encoding="utf-8").splitlines() if environment_path.exists() else []


def parse(lines):
    values = {}
    order = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        values[key] = value
        if key not in order:
            order.append(key)
    return values, order


template_values, template_order = parse(template_lines)
old_values, old_order = parse(old_lines)

# These values describe immutable content in the new payload and must advance
# with it. All other existing values (passwords, tokens and customer integration
# settings) are retained.
release_owned = {
    "BACKEND_IMAGE",
    "POSTGRES_IMAGE",
    "NEO4J_IMAGE",
    "ONTOTWIN_RELEASE_VERSION",
    "ONTOTWIN_DATA_VERSION",
    "ONTOTWIN_HTTP_PORT",
    "ONTOTWIN_BIND_ADDRESS",
    "ARTSTUDIO_BASE_URL",
}
merged = dict(template_values)
for key, value in old_values.items():
    if key not in release_owned:
        merged[key] = value

if merged.get("POSTGRES_PASSWORD") in {None, "", "__POSTGRES_PASSWORD__"}:
    merged["POSTGRES_PASSWORD"] = secrets.token_urlsafe(36)
if merged.get("NEO4J_PASSWORD") in {None, "", "__NEO4J_PASSWORD__"}:
    merged["NEO4J_PASSWORD"] = secrets.token_urlsafe(36)
merged["ONTOTWIN_HTTP_PORT"] = "5000"
merged["ONTOTWIN_BIND_ADDRESS"] = "0.0.0.0"

rendered = []
written = set()
for line in template_lines:
    stripped = line.strip()
    if stripped and not stripped.startswith("#") and "=" in line:
        key = line.split("=", 1)[0].strip()
        rendered.append(f"{key}={merged[key]}")
        written.add(key)
    else:
        rendered.append(line)

# Preserve custom integration keys introduced locally even if the new template
# does not know about them yet.
for key in old_order:
    if key not in written and key not in release_owned:
        rendered.append(f"{key}={merged[key]}")
        written.add(key)

temporary_path = environment_path.with_suffix(".env.new")
temporary_path.write_text("\n".join(rendered) + "\n", encoding="utf-8")
os.chmod(temporary_path, 0o600)
os.replace(temporary_path, environment_path)
PY
chmod 0600 "$persistent_env"
ln -sf "$persistent_env" "$env_file"

cat >/etc/systemd/system/ontotwin-stack.service <<'EOF'
[Unit]
Description=OntoTwin ZHHZ application stack
Wants=network-online.target
After=network-online.target docker.service ontotwin-control.service ontotwin-bootstrap.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ontotwin/release/Deploy
ExecStart=/usr/local/bin/docker compose --env-file .env -f docker-compose.release.yml up -d backend
ExecStop=/usr/local/bin/docker compose --env-file .env -f docker-compose.release.yml stop
TimeoutStartSec=600
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable ontotwin-control.service ontotwin-stack.service
# Reinstall and restart the verified payload copy after the full release and
# persistent environment are in place. This preserves early diagnostics while
# ensuring the long-running service uses the final payload content.
install_control_service
log "Starting the OntoTwin container stack"
if ! compose_output="$(docker compose --env-file "$env_file" \
  -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" up -d backend 2>&1)"; then
  printf '%s\n' "$compose_output"
  compose_summary="$(printf '%s\n' "$compose_output" | tail -n 8 | tr '\n' ' ')"
  log "Bootstrap failed while starting Docker Compose: $compose_summary"
  docker compose --env-file "$env_file" -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" ps --all || true
  docker compose --env-file "$env_file" -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" \
    logs --no-color --tail 80 db neo4j neo4j-init backend || true
  exit 1
fi
printf '%s\n' "$compose_output"
log "OntoTwin services started; waiting for the backend health check"

deadline=$((SECONDS + 300))
until python3 - <<'PY'
import urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5) as response:
        response.read(1)
except Exception:
    # The backend process can reset a probe while Gunicorn is still starting.
    # Return a retry signal without printing a misleading Python traceback.
    raise SystemExit(1)
PY
do
  if [ "$SECONDS" -ge "$deadline" ]; then
    log "Backend health check timed out"
    docker compose --env-file "$env_file" -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" ps --all || true
    docker compose --env-file "$env_file" -f "$RELEASE_ROOT/Deploy/docker-compose.release.yml" \
      logs --no-color --tail 80 db neo4j neo4j-init backend || true
    exit 1
  fi
  sleep 3
done

version="$(awk -F= '$1=="ONTOTWIN_RELEASE_VERSION" {print $2}' "$env_file" | tr -d '\r')"
printf '%s\n' "$version" > "$DATA_ROOT/appliance-content.version"
printf '%s\n' "$payload_fingerprint" > "$PAYLOAD_MARKER.new"
chmod 0600 "$PAYLOAD_MARKER.new"
mv -f "$PAYLOAD_MARKER.new" "$PAYLOAD_MARKER"
rm -f "$BOOTSTRAP_IN_PROGRESS"
python3 - "$HOST_URL/bootstrap/ready" "$version" <<'PY'
import sys
import urllib.request
request = urllib.request.Request(sys.argv[1], data=("ready:" + sys.argv[2]).encode(), method="POST")
urllib.request.urlopen(request, timeout=10).read()
PY
# The stack unit is ordered after ontotwin-bootstrap.service. Queue it without
# blocking so it records the successful state after this bootstrap exits.
systemctl start --no-block ontotwin-stack.service
log "OntoTwin ZHHZ backend is ready"
