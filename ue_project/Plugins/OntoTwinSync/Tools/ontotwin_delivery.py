"""Windows UE editor companion. Standard library only; no backend mutation.

Source identity protocol must match OntoTwinSync.Build.cs. Delivery is an
editable source project, not a packaged executable or a server installer.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
import zipfile


SKIP_DIRS = {"Intermediate", "Saved", "DerivedDataCache", ".git", ".vs", "__pycache__"}
MAX_PACKAGE = 512 * 1024 * 1024


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inside(path, parent):
    return Path(path).resolve().is_relative_to(Path(parent).resolve())


def source_hash(plugin):
    root = Path(plugin)
    files = [p for p in (root / "Source").rglob("*") if p.is_file()]
    files.append(root / "OntoTwinSync.uplugin")
    # C# ordinal ordering is UTF-16; plugin source names are ASCII today.
    files.sort(key=lambda p: p.relative_to(root).as_posix().encode("utf-16-be"))
    lines = "".join(f"{p.relative_to(root).as_posix()}\0{digest(p)}\n" for p in files)
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def plugin_info(plugin):
    root = Path(plugin)
    descriptor = read_json(root / "OntoTwinSync.uplugin")
    resource_files = []
    for name in ("Content", "Resources", "Config", "Tools"):
        if (root / name).is_dir():
            resource_files.extend((p, p.relative_to(root)) for p, _ in inventory(root / name))
    resource_files.sort(key=lambda item: item[1].as_posix())
    resource_hash = hashlib.sha256("".join(f"{rel.as_posix()}\0{digest(p)}\n" for p, rel in resource_files).encode("utf-8")).hexdigest()
    return {"path": str(root.absolute()), "resolved_path": str(root.resolve()), "resource_hash": resource_hash,
            "version": descriptor.get("VersionName", "未标记"), "source_hash": source_hash(root),
            "shared": root.absolute() != root.resolve()}


def version_report(context, mother=None):
    current = plugin_info(context["plugin"])
    loaded = context.get("loaded_hash", "")
    master = plugin_info(mother) if mother else None
    status = "运行构建与磁盘源码一致" if loaded == current["source_hash"] else "源码已变化：需编译并重启 UE"
    if not loaded:
        status = "当前运行构建未知（旧插件未提供标识）"
    return {"project": context["project"], "current": current, "loaded_hash": loaded,
            "runtime_status": status, "mother": master,
            "mother_status": ("与本机母本源码、资源一致" if master["source_hash"] == current["source_hash"] and master["resource_hash"] == current["resource_hash"]
                              else "与本机母本不同（不代表母本更新，更新前检查差异）") if master else "未指定本机母本"}


def inventory(root, omit_binaries=False):
    """Follow junctions into real files, reject cycles and secret files explicitly."""
    root = Path(root)
    result = []

    def walk(folder, ancestors):
        resolved = folder.resolve(strict=True)
        if resolved in ancestors:
            raise ValueError(f"目录链接循环，停止导出：{folder}")
        for p in sorted(folder.iterdir()):
            if p.is_dir():
                if p.name in SKIP_DIRS or (omit_binaries and p.name == "Binaries"):
                    continue
                walk(p, ancestors | {resolved})
            elif p.is_file():
                if p.name.startswith(".env") or p.suffix.lower() in {".pem", ".key", ".pfx"}:
                    raise ValueError(f"发现可能的凭据文件，请先移出交付范围：{p}")
                result.append((p, p.relative_to(root)))
            else:
                raise ValueError(f"无法读取文件或链接：{p}")
    walk(root, set())
    return result


def ensure_destination(destination, roots):
    destination = Path(destination).absolute()
    if destination.exists():
        raise ValueError("输出目录已存在。请选择一个全新的目录，不覆盖原文件。")
    for root in roots:
        if inside(destination, root) or inside(root, destination):
            raise ValueError(f"输出目录不能包含或位于源工程/链接目录内：{root}")
    return destination


def api_bytes(base, route, limit=MAX_PACKAGE):
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("后端地址必须是无用户名密码的 http(s) 地址")
    # Local backends must not accidentally go through the machine's HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if parsed.hostname in {"localhost", "127.0.0.1", "::1"} else urllib.request.build_opener()
    with opener.open(base.rstrip("/") + route, timeout=120) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("响应超过安全大小上限")
    return data


def datasets(base):
    records = json.loads(api_bytes(base, "/api/v2/ontology/datasets", 4 * 1024 * 1024))
    if not isinstance(records, list):
        raise ValueError("后端数据集列表格式不正确")
    return records


def fetch_package(base, dataset_id, ue_id):
    if not ue_id:
        raise ValueError("没有明确的 UE 项目编号。请填写场景管理器的 UEProjectId，不能按当前激活数据集猜测。")
    matches = [d for d in datasets(base) if d.get("id") == dataset_id]
    if len(matches) != 1 or matches[0].get("bound_ue_project_id") != ue_id:
        raise ValueError("所选数据集未绑定当前 UE 编号，停止导出。请在平台确认绑定关系。")
    data = api_bytes(base, "/api/v2/ontology/datasets/" + urllib.parse.quote(dataset_id, safe="") + "/package")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > MAX_PACKAGE:
            raise ValueError("数据集包解压后超过安全大小限制")
        if archive.testzip() is not None:
            raise ValueError("数据集包校验失败")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("delivery_mode") != "project_assets":
            raise ValueError("后端返回的不是包含附件的完整交付包，请先更新后端")
        if (manifest.get("source") or {}).get("dataset_id") != dataset_id:
            raise ValueError("返回的数据集包编号与所选数据集不一致")
        payload = archive.read("project.json")
        if hashlib.sha256(payload).hexdigest() != (manifest.get("payload") or {}).get("sha256"):
            raise ValueError("数据集内容校验失败")
        for attachment in manifest.get("attachments", []):
            if hashlib.sha256(archive.read(attachment["file"])).hexdigest() != attachment["sha256"]:
                raise ValueError("数据集附件校验失败")
    return data


def project_files(project):
    project = Path(project).resolve(strict=True)
    if project.suffix.lower() != ".uproject":
        raise ValueError("请选择 .uproject 文件")
    desc = read_json(project)
    if desc.get("AdditionalPluginDirectories") or desc.get("AdditionalRootDirectories"):
        raise ValueError("工程引用了额外插件/资源目录，需先迁入工程 Plugins/Content 后再导出。")
    entries = [(project, Path(project.name))]
    for name in ("Config", "Content", "Source", "Build", "Plugins", "Art"):
        folder = project.parent / name
        if folder.exists():
            entries.extend((p, Path(name) / rel) for p, rel in inventory(folder))
    return project, desc, entries


def export_project(context, destination, base, dataset_id, ue_id, source_only=False, progress=lambda s: None):
    project, desc, entries = project_files(context["project"])
    plugin = Path(context["plugin"])
    expected = project.parent / "Plugins" / "OntoTwinSync"
    if expected.resolve() != plugin.resolve():
        raise ValueError("当前插件不是工程 Plugins 下的 OntoTwinSync，无法保证独立交付。")
    roots = {project.parent}
    for p, _ in entries:
        for parent in p.parents:
            if parent == project.parent:
                break
            roots.add(parent.resolve())
    output = ensure_destination(destination, roots)
    progress("检查数据集与附件…")
    package = None if source_only else fetch_package(base, dataset_id, ue_id)
    size = sum(p.stat().st_size for p, _ in entries) + len(package or b"")
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < size + 256 * 1024 * 1024:
        raise ValueError("目标磁盘剩余空间不足（预留 256 MB）")
    # Exclusive creation protects against concurrent exports and accidental overwrite.
    output.mkdir()
    marker = output / "EXPORT_INCOMPLETE.txt"
    marker.write_text("交付尚未完成，请勿使用；失败后可保留排查或手动删除此独立目录。", encoding="utf-8")
    records = []
    try:
        for index, (src, relative) in enumerate(entries):
            dst = output / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            before = src.stat()
            shutil.copyfile(src, dst)
            copied_hash = digest(dst)
            if copied_hash != digest(src) or src.stat().st_mtime_ns != before.st_mtime_ns:
                raise ValueError(f"复制期间文件发生变化，请停止保存后重新导出：{relative}")
            records.append({"path": relative.as_posix(), "size": dst.stat().st_size, "sha256": copied_hash})
            if index % 100 == 0:
                progress(f"复制并校验 {index + 1}/{len(entries)}：{relative}")
        # Catch additions/removals and late edits, not only edits during a single copy.
        _, _, final_entries = project_files(project)
        if {str(r) for _, r in final_entries} != {str(r) for _, r in entries}:
            raise ValueError("导出期间源工程文件列表变化，请重新导出")
        progress("复核源文件未变化…")
        for (src, _), record in zip(entries, records):
            if digest(src) != record["sha256"]:
                raise ValueError(f"导出期间源文件变化：{record['path']}")
        delivery = output / "OntoTwinDelivery"
        delivery.mkdir()
        if package is not None:
            (delivery / "project.otdataset").write_bytes(package)
        versions = version_report(context)
        plugin_descriptors = []
        for _, relative in entries:
            if relative.suffix == ".uplugin":
                descriptor = read_json(output / relative)
                plugin_descriptors.append({"path": relative.as_posix(), "version": descriptor.get("VersionName"),
                                           "dependencies": descriptor.get("Plugins", [])})
        manifest = {"schema": 1, "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "kind": "editable-source-project", "engine_association": desc.get("EngineAssociation"),
                    "versions": versions, "dataset_id": None if source_only else dataset_id,
                    "ue_project_id": ue_id, "dataset_sha256": hashlib.sha256(package).hexdigest() if package else None,
                    "files": records, "requires_rebuild": True, "plugin_descriptors": plugin_descriptors,
                    "notes": ["这是可编辑工程，不是已打包程序。请在目标机重编译，不承诺复制的旧 DLL 与源码一致。",
                              "引擎级第三方插件不会自动携带，请按依赖清单安装。",
                              "外部视频网关、实时接口、绝对路径引用与商业资源授权需另行配置。"],
                    "project_plugin_requirements": desc.get("Plugins", [])}
        write_json(delivery / "manifest.json", manifest)
        (delivery / "交付说明.md").write_text(
            "# OntoTwin 可编辑工程交付\n\n"
            "1. 安装与源工程一致的 UE、C++ 编译工具链和引擎级第三方插件。\n"
            "2. 为工程生成项目文件并编译 Development Editor，再打开工程；不要把旧 DLL 当成已验证的新版本。\n"
            "3. 启动兼容版本 OntoTwin 后端，在“导入数据集包”导入 project.otdataset，并确认绑定此工程的 UE 编号。\n"
            "4. 核对后端地址、视频网关和其他外部服务，验收漫游、空间跳转、底图及业务交互。\n\n"
            + ("本次明确选择仅工程，未带数据集/底图。\n" if source_only else "数据集及其附件随 project.otdataset 提供；不是仅拷 UE 插件。\n")
            + "\n所有工程内目录链接已展开为真实文件。版本及逐文件校验见 manifest.json。\n", encoding="utf-8")
        marker.unlink()
        progress(f"导出完成：{output}（目标机需编译与验收）")
        return manifest
    except Exception:
        progress(f"导出未完成，原工程未改动。诊断副本保留在：{output}")
        raise


def editors_running():
    if os.name != "nt":
        raise ValueError("更新安全检查仅支持 Windows")
    result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise ValueError("无法确认 UE 已关闭，停止更新")
    return b"unrealeditor" in result.stdout.lower()


def update_copy(plugin, mother, progress=lambda s: None):
    target, master = Path(plugin).absolute(), Path(mother).resolve(strict=True)
    if target.resolve() == master:
        raise ValueError("当前工程共享母本，不需要复制更新；源码变化后请关闭 UE、编译并重新打开。")
    if target.resolve() != target or inside(master, target) or inside(target, master):
        raise ValueError("目标是链接目录或与母本嵌套，禁止替换；请先明确插件来源。")
    plugin_info(target)
    plugin_info(master)
    if editors_running():
        raise ValueError("请先关闭所有 UE 编辑器，再点击更新。本窗口可以保持打开。")
    token = uuid.uuid4().hex[:10]
    # Keep backups outside Plugins: otherwise UE discovers duplicate .uplugin files.
    backups = target.parent.parent / "Saved" / "OntoTwinPluginBackups"
    backups.mkdir(parents=True, exist_ok=True)
    stage, backup = backups / ("prepared-" + token), backups / ("previous-" + token)
    stage.mkdir()
    entries = inventory(master, omit_binaries=True)
    copied = []
    for src, rel in entries:
        dest = stage / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        copied_hash = digest(dest)
        if digest(src) != copied_hash:
            raise ValueError("母本在复制期间变化，未替换原插件")
        copied.append((src, copied_hash))
    if source_hash(stage) != source_hash(master):
        raise ValueError("母本源码变化，请重新更新")
    if [rel for _, rel in entries] != [rel for _, rel in inventory(master, omit_binaries=True)]:
        raise ValueError("母本文件列表变化，请重新更新")
    if any(digest(src) != value for src, value in copied):
        raise ValueError("母本资源变化，请重新更新")
    if editors_running():
        raise ValueError("检测到 UE 重新打开，未替换原插件")
    target.rename(backup)
    try:
        stage.rename(target)
    except Exception:
        backup.rename(target)
        raise
    progress(f"已更新源码与资源；旧插件完整保存在 {backup}。下一步：编译并重启 UE。")
    return backup


def rebuild(context, progress=lambda s: None):
    if editors_running():
        raise ValueError("请先关闭所有 UE 编辑器，再编译更新")
    engine = Path(context["engine"])
    runtimes = sorted((engine / "Binaries/ThirdParty/DotNet").glob("*/win-x64/dotnet.exe"))
    ubt = engine / "Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll"
    if not runtimes or not ubt.is_file():
        raise ValueError("找不到 UE 内置编译工具。请确认完整安装 UE 5.6 与 Visual Studio C++ 工具链。")
    project = Path(context["project"]).resolve(strict=True)
    targets = sorted((project.parent / "Source").glob("*Editor.Target.cs"))
    if len(targets) > 1:
        raise ValueError("工程有多个 Editor 编译目标，请在 Visual Studio 明确选择后编译")
    target = targets[0].name.removesuffix(".Target.cs") if targets else "UnrealEditor"
    log_dir = project.parent / "Saved/OntoTwinDelivery"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / ("build-" + time.strftime("%Y%m%d-%H%M%S") + ".log")
    args = [str(runtimes[-1]), str(ubt), target, "Win64", "Development", "-Project=" + str(project), "-WaitMutex", "-NoHotReloadFromIDE"]
    progress("开始编译，请等待。日志：" + str(log_path))
    with log_path.open("w", encoding="utf-8") as log:
        with subprocess.Popen(args, cwd=engine / "Source", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW) as process:
            for line in process.stdout:
                log.write(line)
                log.flush()
                progress(line.rstrip())
            code = process.wait()
    if code:
        raise ValueError(f"编译失败（{code}），未宣称更新完成。日志：{log_path}")
    progress("编译成功。请重新打开 UE，再从工具菜单检查版本（本窗口运行标识仍是启动时快照）。")


def launch_gui(context):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.title("OntoTwin · 插件版本与交付")
    root.geometry("920x760")
    root.minsize(820, 650)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=("Microsoft YaHei UI", 10))
    style.configure("TFrame", background="#f5f5f5")
    style.configure("TLabel", background="#f5f5f5", foreground="#222222")
    outer = ttk.Frame(root, padding=18)
    outer.pack(fill="both", expand=True)
    ttk.Label(outer, text="插件版本与更新 / 导出交付工程", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
    ttk.Label(outer, text="当前工程：" + context["project"], wraplength=860).pack(anchor="w", pady=(8, 12))
    config_file = Path(context["project"]).parent / "Saved" / "OntoTwinDelivery" / "preferences.json"
    settings = read_json(config_file) if config_file.exists() else {}
    inferred = Path(context["plugin"]).resolve()
    default_mother = str(inferred) if (inferred.parent.parent.parent / "backend").is_dir() else ""
    mother = tk.StringVar(value=settings.get("mother", default_mother))
    base = tk.StringVar(value=context.get("backend") or "http://localhost:5000")
    ue_id = tk.StringVar(value=context.get("ue_id", ""))
    selected = tk.StringVar()
    output = tk.StringVar(value=str(Path(context["project"]).parent.parent / (Path(context["project"]).stem + "_delivery_" + time.strftime("%Y%m%d_%H%M%S"))))
    source_only = tk.BooleanVar(value=False)
    events = queue.Queue()
    busy = [False]
    ds_records = []

    def row(label, variable, browse=False):
        frame = ttk.Frame(outer)
        frame.pack(fill="x", pady=4)
        ttk.Label(frame, text=label, width=17).pack(side="left")
        ttk.Entry(frame, textvariable=variable).pack(side="left", fill="x", expand=True)
        if browse:
            def choose():
                path = filedialog.askdirectory(parent=root)
                if path:
                    variable.set(path)
            ttk.Button(frame, text="选择", command=choose).pack(side="right", padx=(8, 0))
    row("本机母本插件目录", mother, True)
    row("后端地址", base)
    row("当前 UE 项目编号", ue_id)
    ds_row = ttk.Frame(outer)
    ds_row.pack(fill="x", pady=4)
    ttk.Label(ds_row, text="交付数据集", width=17).pack(side="left")
    ds_combo = ttk.Combobox(ds_row, textvariable=selected, state="readonly")
    ds_combo.pack(side="left", fill="x", expand=True)
    row("输出新目录", output)
    ttk.Checkbutton(outer, text="仅导出 UE 工程（明确不带数据集、CAD 与图片底图）", variable=source_only).pack(anchor="w", pady=6)
    ttk.Label(outer, text="导出是独立可编辑工程，不是打包程序。先保存所有资产，导出期间不要保存或改动文件。\n母本仅指所选本机目录；差异不代表谁更新。不自动拉取 main，也不热替换运行中的 DLL。", wraplength=860).pack(anchor="w", pady=6)
    buttons = ttk.Frame(outer)
    buttons.pack(fill="x", pady=8)
    report = tk.Text(outer, wrap="word", background="#ffffff", foreground="#222222", relief="flat", padx=12, pady=10, font=("Microsoft YaHei UI", 10))
    report.pack(fill="both", expand=True)
    report.configure(state="disabled")
    status = tk.StringVar(value="就绪")
    ttk.Label(outer, textvariable=status, wraplength=860).pack(anchor="w", pady=(8, 0))

    def log(text):
        report.configure(state="normal")
        report.insert("end", text + "\n")
        report.see("end")
        report.configure(state="disabled")

    def run(work):
        if busy[0]:
            return
        busy[0] = True
        status.set("处理中…")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        write_json(config_file, {"mother": mother.get().strip()})
        def worker():
            try:
                work()
            except Exception as exc:
                events.put(("error", str(exc)))
            finally:
                events.put(("done", None))
        threading.Thread(target=worker, daemon=False).start()

    def emit(text):
        events.put(("log", text))

    def check():
        path = mother.get().strip()
        def work():
            r = version_report(context, path or None)
            c = r["current"]
            emit(f"\n本工程：{c['version']} · 源码 {c['source_hash'][:12]} · 资源 {c['resource_hash'][:12]}\n实际运行构建：{r['loaded_hash'][:12] or '未知'}\n{r['runtime_status']}\n插件来源：{'共享母本（链接）' if c['shared'] else '独立目录'}\n真实路径：{c['resolved_path']}")
            if r["mother"]:
                m = r["mother"]
                emit(f"本机母本：{m['version']} · 源码 {m['source_hash'][:12]} · 资源 {m['resource_hash'][:12]}\n{r['mother_status']}")
            else:
                emit(r["mother_status"])
            emit("注：源码编号随 Source / uplugin 内容改变；资产变化以交付清单逐文件校验为准。运行标识是打开本窗口时的 UE 快照。")
        run(work)

    def load_datasets():
        address, identity = base.get().strip(), ue_id.get().strip()
        def work():
            records = [d for d in datasets(address) if d.get("id") != "demo"]
            events.put(("datasets", (records, identity)))
        run(work)

    def export():
        args = (output.get().strip(), base.get().strip(), selected.get().split(" | ")[0], ue_id.get().strip(), source_only.get())
        if not args[0] or (not args[4] and not args[2]):
            messagebox.showwarning("未准备好", "请填写输出目录，并读取/选择绑定数据集。", parent=root)
            return
        if messagebox.askokcancel("确认交付范围", "已保存工程？\n\n将复制整个工程的 Content、Config、Source、Build、Plugins、Art，展开目录链接。\n不会修改原工程；不会自动安装引擎级插件或外部视频服务。\n\n输出：" + args[0], parent=root):
            run(lambda: export_project(context, *args, progress=emit))

    def update():
        path = mother.get().strip()
        if not path:
            messagebox.showwarning("选择母本", "请先选择母本插件目录。", parent=root)
            return
        if messagebox.askokcancel("更新独立插件副本", "请先关闭所有 UE 编辑器，可保留本窗口。\n\n所选母本将替换此工程插件（含本地改动）。旧目录会完整备份，不复制 DLL；更新后必须重新编译。\n若是共享母本，无需复制。", parent=root):
            run(lambda: update_copy(context["plugin"], path, emit))

    def compile_update():
        if messagebox.askokcancel("编译工程插件", "请先关闭所有 UE 编辑器。\n\n将使用当前 UE 安装编译本工程，需要 Visual Studio C++ 工具链；不会打开编辑器或改变数据集。", parent=root):
            run(lambda: rebuild(context, emit))

    ttk.Button(buttons, text="检查版本", command=check).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="读取数据集", command=load_datasets).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="更新独立副本", command=update).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="编译更新", command=compile_update).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="导出交付工程", command=export).pack(side="left")

    def poll():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == "log":
                    log(value)
                    status.set(value)
                elif kind == "error":
                    log("未完成：" + value)
                    status.set("未完成，请查看原因")
                elif kind == "done":
                    busy[0] = False
                elif kind == "datasets":
                    records, identity = value
                    ds_records[:] = records
                    labels = [f"{d['id']} | {d.get('name', '')} | UE: {d.get('bound_ue_project_id') or '未绑定'}" for d in records]
                    ds_combo["values"] = labels
                    matches = [i for i, d in enumerate(records) if identity and d.get("bound_ue_project_id") == identity]
                    selected.set(labels[matches[0]] if len(matches) == 1 else "")
                    log("已读取数据集；" + ("已按 UE 编号匹配，未改变平台激活状态。" if len(matches) == 1 else "没有唯一匹配，请确认 UE 编号和绑定关系。"))
        except queue.Empty:
            pass
        root.after(150, poll)

    def close():
        if busy[0]:
            messagebox.showinfo("正在处理", "为保证文件完整，请等本次操作结束后关闭。", parent=root)
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", close)
    poll()
    check()
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    args = parser.parse_args()
    launch_gui(read_json(args.context))
