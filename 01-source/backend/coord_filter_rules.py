"""
PRD 2.9.2 § 6 — DXF 块过滤规则

两层过滤：图层黑名单 + block_name 前缀黑名单。
另定义灰色地带（`0` 图层标红、`0XX` 标黄）供 UI 警告。

修改这里的规则后无需改业务代码。
"""
import re

# ── 图层黑名单 ──────────────────────────────────────────────

LAYER_BLACKLIST_EXACT = {'Defpoints'}

LAYER_BLACKLIST_PREFIXES = ('A-', 'PUB_', 'DIM_')

# 含这些子串 → XREF 外参图层
LAYER_XREF_MARKERS = ('$0$', '$AZ$')


def is_layer_blacklisted(layer: str):
    """返回 (是否过滤, 原因字符串)。原因仅在过滤时返回。"""
    if not layer:
        return False, None
    if layer in LAYER_BLACKLIST_EXACT:
        return True, 'AutoCAD 系统层'
    for p in LAYER_BLACKLIST_PREFIXES:
        if layer.startswith(p):
            return True, f'AIA 标准/公共图层（前缀 {p}）'
    for marker in LAYER_XREF_MARKERS:
        if marker in layer:
            return True, f'XREF 外参图层（含 {marker}）'
    return False, None


# ── block_name 黑名单 ───────────────────────────────────────

BLOCK_BLACKLIST_EXACT = {'_AXISO'}

# (前缀, 原因)
BLOCK_BLACKLIST_PREFIXES = (
    ('A$C', 'AutoCAD 匿名块'),
    ('A$c', 'AutoCAD 匿名块'),
    ('*U',  'AutoCAD 匿名块'),
    ('G$C', '匿名块'),
    ('zw$', '中望 CAD 内部块'),
    ('template_', '图框/模板块'),
    ('AE_A0',     '图框/模板块'),
)

# block_name 中含这些子串 → XREF 外参子块
BLOCK_XREF_MARKERS = ('$0$', '$AZ$')


def is_block_blacklisted(block_name: str):
    """返回 (是否过滤, 原因字符串)。"""
    if not block_name:
        return False, None
    if block_name in BLOCK_BLACKLIST_EXACT:
        return True, '坐标轴/系统辅助块'
    for prefix, reason in BLOCK_BLACKLIST_PREFIXES:
        if block_name.startswith(prefix):
            return True, reason
    for marker in BLOCK_XREF_MARKERS:
        if marker in block_name:
            return True, f'XREF 外参子块（含 {marker}）'
    return False, None


# ── 灰色地带（不过滤，仅 UI 警告）─────────────────────────────

# 完全等于这些 → 红色警告：默认不勾选
GRAY_LAYERS_RED = {'0', '00'}

# 满足这些正则 → 黄色警告：默认勾选但需用户复核
GRAY_LAYERS_YELLOW_PATTERNS = (
    re.compile(r'^0[一-鿿]'),    # 0+中文，如 "0土建原始墙"、"0土建门"
    re.compile(r'^00[一-鿿]'),   # 00+中文
    re.compile(r'^000[一-鿿]'),  # 000+中文，如 "000家具" "000卫生间洁具"
    re.compile(r'^弱电图层$'),
    re.compile(r'^1平面隔墙$'),          # 0/1 开头的怪图层
)


def classify_layer(layer: str):
    """
    返回 (warning_color, warning_text, default_checked)。

    - warning_color: None | "red" | "yellow"
    - warning_text:  None | 提示文案
    - default_checked: 候选条目默认勾选状态
    """
    if not layer:
        return None, None, True
    if layer in GRAY_LAYERS_RED:
        return 'red', f'位于 "{layer}" 图层（未分图层，请仔细确认）', False
    for pat in GRAY_LAYERS_YELLOW_PATTERNS:
        if pat.search(layer):
            return 'yellow', f'图层 "{layer}" 归属可疑，请复核', True
    return None, None, True
