"""本地文件校验与读取 —— 供 DXF/CSV 上传类工具使用。

安全边界（spec §7）：规范化路径防 `..` 穿越、限 allowed_roots、限扩展名、限大小，
返回**原始 basename**（后端 CSV 按 filename 识别 6 表，须保真）+ 文件字节内容。
"""
import os


def _under_root(real: str, root: str) -> bool:
    """判断 real 是否落在 root（均取 realpath 后比对）内。

    跨盘符时 os.path.commonpath 会抛 ValueError（Windows），视为“不在 root 内”。
    """
    root_real = os.path.realpath(root)
    try:
        return os.path.commonpath([real, root_real]) == root_real
    except ValueError:
        # 不同盘符 / 无公共前缀 → 不在该 root 内
        return False


def resolve_upload(file_path, settings, allowed_ext=None, max_bytes=50_000_000):
    """校验并读取本地文件，返回 (原始 basename, 文件字节)。违规抛 ValueError（中文原因）。"""
    real = os.path.realpath(os.path.abspath(file_path))
    if not os.path.exists(real) or not os.path.isfile(real):
        raise ValueError(f"文件不存在或非普通文件: {file_path}")
    # 空 allowed_roots = 不限制（本地开发默认）
    if settings.allowed_roots:
        ok = any(_under_root(real, r) for r in settings.allowed_roots)
        if not ok:
            raise ValueError(f"路径不在允许目录内（NEXUS_ALLOWED_ROOTS）: {file_path}")
    base = os.path.basename(real)
    if allowed_ext and os.path.splitext(base)[1].lower() not in allowed_ext:
        raise ValueError(f"不支持的扩展名: {base}（允许 {allowed_ext}）")
    size = os.path.getsize(real)
    if size > max_bytes:
        raise ValueError(f"文件过大: {size} > {max_bytes}")
    # 注：先校验（exists/root/ext/size）后打开，存在极窄的 TOCTOU 窗口——
    # 校验与 open 之间文件可能被替换。单用户本地场景可接受；前提是
    # allowed_roots 目录不应对低权限用户可写（否则可借符号链接绕过校验）。
    with open(real, "rb") as f:
        return base, f.read()
