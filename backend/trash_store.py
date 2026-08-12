"""
TrashStore — 文件后端的"回收站"。

作用：把 project_store 里"物理删除/覆写"三个动作变成两步 —— 先快照到回收站，再执行。
    kind=project    快照整份 project JSON
    kind=scene      快照 { project_id, instances }（scene/clear 前的 instances 全集）
    kind=instance   快照 { project_id, instance_id, record }（单实例记录）

存储：
    data/trash/
        index.json                    # 全部条目元数据（列表）
        projects/<trash_id>.json      # 快照文件
        scenes/<trash_id>.json
        instances/<trash_id>.json

TTL：默认 90 天，从 deleted_at_ts 起算。启动时以及每次 list 时顺带清理过期项。
恢复策略：覆盖（用户已确认，无对话式冲突处理）。
"""

import json
import os
import time
import threading
import copy
import secrets


DEFAULT_TTL_SECONDS = 90 * 24 * 3600

_KINDS = ("project", "scene", "instance")


class TrashError(Exception):
    pass


class TrashStore:
    def __init__(self, root_dir=None, ttl_seconds=DEFAULT_TTL_SECONDS):
        self._lock = threading.RLock()
        self._root = root_dir or os.path.join(os.path.dirname(__file__), "data", "trash")
        self._index_file = os.path.join(self._root, "index.json")
        self._ttl = int(ttl_seconds)
        os.makedirs(self._root, exist_ok=True)
        for k in _KINDS:
            os.makedirs(os.path.join(self._root, k + "s"), exist_ok=True)

    # ── 底层 IO ─────────────────────────────────────────────────
    def _write_json(self, path, obj):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, path)

    def _read_index(self):
        if not os.path.exists(self._index_file):
            return {"items": []}
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                return {"items": []}
            return data
        except Exception:
            return {"items": []}

    def _save_index(self, data):
        self._write_json(self._index_file, data)

    def _snapshot_path(self, kind, trash_id):
        return os.path.join(self._root, kind + "s", trash_id + ".json")

    def _new_id(self, kind):
        return f"{kind}_{int(time.time() * 1000)}_{secrets.token_hex(3)}"

    # ── 写入 ────────────────────────────────────────────────────
    def put(self, kind, payload, *, project_id=None, name=None,
            instance_id=None, instance_count=None, note=""):
        if kind not in _KINDS:
            raise TrashError(f"unknown kind: {kind}")
        with self._lock:
            trash_id = self._new_id(kind)
            self._write_json(self._snapshot_path(kind, trash_id), payload)
            entry = {
                "id": trash_id,
                "kind": kind,
                "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "deleted_at_ts": int(time.time()),
                "project_id": project_id,
                "name": name,
                "instance_id": instance_id,
                "instance_count": instance_count,
                "note": note or "",
            }
            idx = self._read_index()
            idx["items"].append(entry)
            self._save_index(idx)
            return entry

    # ── 读取 ────────────────────────────────────────────────────
    def list_items(self):
        with self._lock:
            self.sweep_expired()
            idx = self._read_index()
            items = list(idx["items"])
        items.sort(key=lambda x: x.get("deleted_at_ts", 0), reverse=True)
        return items

    def get_entry(self, trash_id):
        with self._lock:
            idx = self._read_index()
            for it in idx["items"]:
                if it.get("id") == trash_id:
                    return dict(it)
            return None

    def get_snapshot(self, trash_id):
        """返回 (entry, payload)；不存在时返回 (None, None)。"""
        with self._lock:
            entry = self.get_entry(trash_id)
            if not entry:
                return None, None
            path = self._snapshot_path(entry["kind"], trash_id)
            if not os.path.exists(path):
                return entry, None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception:
                payload = None
            return entry, payload

    # ── 删除 ────────────────────────────────────────────────────
    def delete(self, trash_id):
        """永久删除单条。"""
        with self._lock:
            idx = self._read_index()
            entry = next((it for it in idx["items"] if it.get("id") == trash_id), None)
            if entry is None:
                return False
            idx["items"] = [it for it in idx["items"] if it.get("id") != trash_id]
            self._save_index(idx)
            path = self._snapshot_path(entry["kind"], trash_id)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            return True

    def purge_all(self):
        """清空全部。返回删除条数。"""
        with self._lock:
            idx = self._read_index()
            n = len(idx["items"])
            for it in list(idx["items"]):
                path = self._snapshot_path(it["kind"], it["id"])
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            self._save_index({"items": []})
            return n

    def sweep_expired(self):
        """按 TTL 清理过期条目。返回删除条数。"""
        if self._ttl <= 0:
            return 0
        cutoff = int(time.time()) - self._ttl
        with self._lock:
            idx = self._read_index()
            keep, drop = [], []
            for it in idx["items"]:
                if int(it.get("deleted_at_ts", 0)) < cutoff:
                    drop.append(it)
                else:
                    keep.append(it)
            if not drop:
                return 0
            for it in drop:
                path = self._snapshot_path(it["kind"], it["id"])
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            idx["items"] = keep
            self._save_index(idx)
            return len(drop)


# 模块级单例：与 project_store 相同的默认根目录
_default_store = None


def get_default_store():
    global _default_store
    if _default_store is None:
        _default_store = TrashStore()
    return _default_store
