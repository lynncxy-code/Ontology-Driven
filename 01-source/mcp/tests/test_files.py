import os
import pytest
from ontotwin_mcp.files import resolve_upload
from ontotwin_mcp.config import Settings


def test_reads_and_keeps_basename(tmp_path):
    p = tmp_path / "objectdef.csv"
    p.write_bytes("a".encode("utf-8-sig"))
    s = Settings(allowed_roots=[str(tmp_path)])
    name, content = resolve_upload(str(p), s, allowed_ext=[".csv"])
    assert name == "objectdef.csv" and content.startswith(b"\xef\xbb\xbf")


def test_outside_allowed_roots_rejected(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("x")
    s = Settings(allowed_roots=["/nonexistent-root"])
    with pytest.raises(ValueError):
        resolve_upload(str(p), s, allowed_ext=[".csv"])


def test_bad_ext_rejected(tmp_path):
    p = tmp_path / "x.exe"
    p.write_text("x")
    s = Settings(allowed_roots=[str(tmp_path)])
    with pytest.raises(ValueError):
        resolve_upload(str(p), s, allowed_ext=[".csv"])


def test_missing_file_rejected(tmp_path):
    s = Settings(allowed_roots=[str(tmp_path)])
    with pytest.raises(ValueError):
        resolve_upload(str(tmp_path / "nope.csv"), s, allowed_ext=[".csv"])


def test_empty_allowed_roots_unrestricted(tmp_path):
    # 空 allowed_roots = 不限制（本地开发默认）
    p = tmp_path / "linkdef.csv"
    p.write_text("x")
    s = Settings(allowed_roots=[])
    name, content = resolve_upload(str(p), s, allowed_ext=[".csv"])
    assert name == "linkdef.csv"


def test_traversal_escape_rejected(tmp_path):
    # 表面在 allowed root 下、实则通过 .. 逃逸的路径必须被拒
    safe = tmp_path / "safe"
    safe.mkdir()
    secret = tmp_path / "secret.csv"
    secret.write_text("leak")
    # 路径穿过 safe 目录，但用 .. 逃回上级取 secret.csv
    sneaky = os.path.join(str(safe), "..", "secret.csv")
    s = Settings(allowed_roots=[str(safe)])
    with pytest.raises(ValueError):
        resolve_upload(sneaky, s, allowed_ext=[".csv"])


@pytest.mark.skipif(os.name != "nt", reason="跨盘符仅在 Windows 有意义")
def test_cross_drive_rejected(tmp_path):
    # allowed_root 在另一盘符时，commonpath 会抛 ValueError；应视为“不在允许目录内”而拒绝
    p = tmp_path / "x.csv"
    p.write_text("x")
    cur_drive = os.path.splitdrive(str(tmp_path))[0].upper()  # e.g. "D:"
    other = "Z:" if cur_drive != "Z:" else "Y:"
    s = Settings(allowed_roots=[other + os.sep + "some-root"])
    with pytest.raises(ValueError):
        resolve_upload(str(p), s, allowed_ext=[".csv"])
