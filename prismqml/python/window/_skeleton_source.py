# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Automatic skeleton layout inference from page QML source. 从页面 QML 源码自动推断骨架布局。

The lazy-loading skeleton must mirror the shape of the page being awaited, but the
page object does not exist yet (its Loader is inactive until the switch completes),
and QML cannot read local source files unless the host enables
`QML_XHR_ALLOW_FILE_READ`. The engine therefore infers the layout here, in Python,
from the page's own QML text, and hands the result to the QML renderer through an
injectable resolver.
懒加载骨架必须贴合被等待页面的形状，但页面对象此刻尚不存在（其 Loader 在切换完成前
不激活），且 QML 读本地源码依赖宿主开启 `QML_XHR_ALLOW_FILE_READ`。因此由引擎在此处
用 Python 从页面自身的 QML 文本推断布局，并经可注入解析器交给 QML 渲染层。
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Slot

from ..core.logger import debug, warning
from ..core.utils import qml_path

# The skeleton is a non-scrolling overlay, so only the first screen is mirrored.
# These caps keep the overlay from growing without bound on long pages.
# 骨架是非滚动遮罩，因此只镜像首屏。这些上限避免长页面让骨架无限增长。
MAX_CARDS = 4
MAX_BLOCKS = 24
MAX_CARD_CHILDREN = 6

SKELETON_ENUM_SOURCE = "PrismEnums/Skeleton.qml"

# Containers rendered as one card that holds its own children. 渲染为带子块卡片的容器。
CARD_CONTAINERS = frozenset({"ExampleCard", "SettingsCardGroup"})

# Markers that introduce a labelled sub-section inside a card. 卡片内引入带标签分节的标记。
SUBTITLE_MARKERS = frozenset({"ComponentCard"})

# Leaf controls grouped by the block type they stand for. 按所代表块类型归类的叶子控件。
LEAF_BLOCK_GROUPS = {
    "block_input": (
        "LineEdit", "TextField", "SpinBox", "ComboBox", "ComboBoxEntry",
        "DatePicker", "DateTimePicker", "ColorPicker", "SearchBar", "Slider",
        "ToggleSwitch", "CheckBox", "RadioButton", "Rating",
    ),
    "block_list": ("ListWidget", "ListView", "TreeWidget", "RepeaterView"),
    "block_table": ("TableWidget", "TableView", "DataGrid"),
    "block_chart": (
        "Chart", "ChartView", "LineChart", "BarChart", "PieChart", "RadarChart",
        "BoxplotChart", "CircularGauge", "Gauge", "ProgressBar", "ProgressRing",
        "Sparkline",
    ),
    "block_carousel": ("Carousel", "SwipeView"),
    "block_avatar": ("Avatar",),
    "block_icon": ("Icon", "HintIcon"),
    "block_image": ("Image", "AnimatedImage"),
    "block_divider": ("Divider", "MenuSeparator", "Separator"),
    "block_tabs": ("TabView", "TabBar", "Pivot", "SegmentedControl"),
    "block_listItem": ("SettingsCard", "ListWidgetItem"),
    "block_text": ("Label", "Breadcrumb", "Marquee", "Badge", "Tag", "ToolTip"),
}

# Reverse index: component name -> block enum name. 反查表: 组件名 -> 块枚举名。
LEAF_BLOCK_BY_NAME = {
    component: block
    for block, components in LEAF_BLOCK_GROUPS.items()
    for component in components
}

# Horizontal containers whose repeated buttons read as one button row.
# 内部重复按钮读作一个按钮行的横向容器。
ROW_CONTAINERS = frozenset({"Flow", "Row", "GalleryFlow"})

_ENUM_RE = re.compile(r"readonly\s+property\s+int\s+(block_\w+)\s*:\s*(\d+)")
# One pass finds every "identifier followed by { or :" plus every bare brace. The
# pattern deliberately has no nested quantifier: a dotted-path form such as
# `(?:\.[A-Za-z_]\w*)*` backtracks on every dotted expression in the file and cost
# ~5ms per page. Matching the last path component instead is linear, and the dotted
# continuations are rejected by `_is_property_position`.
# 单次扫描找出所有"标识符后跟 { 或 :"以及所有裸花括号。该模式刻意不含嵌套量词: 形如
# `(?:\.[A-Za-z_]\w*)*` 的点号路径形式会在文件里每个点号表达式上回溯, 每页约 5ms。
# 改为只匹配路径末段则是线性的, 点号续段由 `_is_property_position` 排除。
_EVENT_RE = re.compile(r"([A-Za-z_]\w*)[ \t]*([:{])|([{}])")

_enum_values: dict[str, int] | None = None
_block_cache: dict[str, list] = {}


def block_type_values() -> dict[str, int]:
    """Every `block_*` enum, read from the QML single source. 从 QML 单一来源读取全部块枚举。"""
    global _enum_values
    if _enum_values is None:
        _enum_values = _load_block_type_values()
    return _enum_values


def _load_block_type_values() -> dict[str, int]:
    try:
        source = qml_path(SKELETON_ENUM_SOURCE).read_text(encoding="utf-8")
    except OSError as error:
        warning(f"骨架枚举读取失败 Skeleton enum read failed: {error}")
        return {}
    return {name: int(value) for name, value in _ENUM_RE.findall(source)}


def _type(enum_name: str) -> int:
    """Numeric value of one block enum; -1 when the single source lacks it."""
    return block_type_values().get(enum_name, -1)


# Line comments, block comments and both string forms, blanked in one C-speed pass.
# 行注释、块注释与两种字符串形式，一次 C 速度扫描统一抹除。
_NOISE_RE = re.compile(
    r"//[^\n]*"
    r"|/\*.*?\*/"
    r'|"(?:\\.|[^"\\\n])*"'
    r"|'(?:\\.|[^'\\\n])*'",
    re.DOTALL,
)
_NON_NEWLINE_RE = re.compile(r"[^\n]")


def _strip_noise(source: str) -> str:
    """Blank out comments and string bodies, preserving every offset. 抹掉注释与字符串内容并保留偏移。"""
    return _NOISE_RE.sub(lambda match: _blank(match.group(0)), source)


def _blank(text: str) -> str:
    """Spaces of identical length, keeping newlines so offsets stay aligned."""
    if "\n" not in text:
        return " " * len(text)
    return _NON_NEWLINE_RE.sub(" ", text)


def _pop_to(stack: list, depth: int, position: int) -> None:
    """Close every object the current depth has left behind. 关闭当前深度已离开的所有对象。"""
    while len(stack) > 1 and depth < stack[-1][1]:
        stack.pop()[0]["end"] = position


def _is_property_position(source: str, start: int) -> bool:
    """True when a `name:` sits at statement level, not inside a ternary.

    仅当 `name:` 位于语句层级（而非三元表达式内部）时为真。
    """
    index = start - 1
    while index >= 0 and source[index] in " \t":
        index -= 1
    return index < 0 or source[index] in "\n{,;"


def _apply_event(event, source: str, stack: list, depth: int) -> int:
    """Apply one scan event and return the new brace depth. 处理一个扫描事件并返回新的括号深度。"""
    token = event.group(1)
    if token is None:
        if event.group(3) == "{":
            return depth + 1
        _pop_to(stack, depth - 1, event.start())
        return depth - 1
    if event.group(2) == "{":
        head = token.split(".")[-1]
        if head[:1].isupper():
            node = {
                "name": head,
                "props": {},
                "children": [],
                "body_start": event.end(),
                "end": len(source),
            }
            stack[-1][0]["children"].append(node)
            stack.append((node, depth + 1))
        return depth + 1
    if depth == stack[-1][1] and _is_property_position(source, event.start()):
        stack[-1][0]["props"].setdefault(token, event.end())
    return depth


def _scan(source: str) -> dict:
    """Object tree plus depth-1 property offsets. 对象树与一层属性偏移。"""
    root = {"name": "<root>", "props": {}, "children": [], "end": len(source)}
    stack = [(root, 0)]
    depth = 0
    for event in _EVENT_RE.finditer(source):
        depth = _apply_event(event, source, stack, depth)
    while len(stack) > 1:
        stack.pop()[0]["end"] = len(source)
    # Unbalanced braces mean truncated or corrupted source: no usable structure.
    # 花括号不配对说明源码被截断或损坏: 无可用结构。
    if depth != 0:
        return None
    return root


def _prop_text(node: dict, source: str, name: str) -> str:
    """Raw value text of one depth-1 property, or "" when absent. 一层属性的原始值文本。"""
    start = node["props"].get(name)
    if start is None:
        return ""
    ends = [offset for offset in node["props"].values() if offset > start]
    end = min(min(ends), node["end"]) if ends else node["end"]
    return source[start:end].strip().rstrip(",;")


def _has_text(value: str) -> bool:
    """True when a property value is a real, non-empty expression. 属性值为真实非空表达式。"""
    trimmed = value.strip()
    return trimmed not in ("", '""', "''", "``")


def _is_page_title(node: dict, source: str) -> bool:
    """A Text sized with `typography.displayLarge` is the page heading."""
    return "typography.displayLarge" in source[node["body_start"]:node["end"]]


def _count_buttons(node: dict, limit: int = 12) -> int:
    """Buttons anywhere inside a container, bounded. 容器内任意深度的按钮数，有上限。"""
    total = 0
    for child in node["children"]:
        if child["name"] == "Button":
            total += 1
        else:
            total += _count_buttons(child, limit)
        if total >= limit:
            return limit
    return total


def _card_block(card: dict, source: str) -> dict:
    """One card plus the children inferred from its real content. 一张卡片及其内容推断子块。"""
    children: list[dict] = []
    if _has_text(_prop_text(card, source, "title")):
        children.append({"type": _type("block_subtitle")})
    if _has_text(_prop_text(card, source, "description")):
        children.append({"type": _type("block_text")})
    _collect_card_content(card, source, children)
    return {"type": _type("block_card"), "children": children}


def _collect_card_content(node: dict, source: str, blocks: list[dict]) -> None:
    """Walk a card's content and emit one block per meaningful child. 遍历卡片内容并逐块产出。"""
    for child in node["children"]:
        if len(blocks) >= MAX_CARD_CHILDREN:
            return
        name = child["name"]
        if name in SUBTITLE_MARKERS:
            if _has_text(_prop_text(child, source, "label")):
                blocks.append({"type": _type("block_subtitle")})
            _collect_card_content(child, source, blocks)
        elif name in ROW_CONTAINERS:
            buttons = _count_buttons(child)
            if buttons >= 2:
                blocks.append({"type": _type("block_buttonRow"), "buttons": buttons})
                continue
            _collect_card_content(child, source, blocks)
        elif name == "Button":
            blocks.append({"type": _type("block_button")})
        elif name in LEAF_BLOCK_BY_NAME:
            blocks.append({"type": _type(LEAF_BLOCK_BY_NAME[name])})
        elif name == "Text":
            blocks.append({"type": _type("block_textLines")})
        else:
            _collect_card_content(child, source, blocks)


def _walk(node: dict, source: str, blocks: list[dict], counters: dict) -> None:
    """Collect the page's first-screen blocks. 收集页面首屏块。"""
    for child in node["children"]:
        if len(blocks) >= MAX_BLOCKS or counters["cards"] >= MAX_CARDS:
            return
        name = child["name"]
        if name == "Text" and _is_page_title(child, source):
            blocks.append({"type": _type("block_title")})
        elif name in CARD_CONTAINERS:
            counters["cards"] += 1
            blocks.append(_card_block(child, source))
        elif name in LEAF_BLOCK_BY_NAME:
            blocks.append({"type": _type(LEAF_BLOCK_BY_NAME[name])})
        else:
            _walk(child, source, blocks, counters)


def infer_blocks(source: str) -> list[dict]:
    """Infer a first-screen skeleton structure from page QML source. 从页面源码推断首屏骨架结构。"""
    try:
        root = _scan(_strip_noise(source))
    except (ValueError, IndexError) as error:
        debug(f"骨架解析失败 Skeleton inference failed: {error}")
        return []
    if root is None:
        debug("骨架源码括号不配对, 回退通用骨架 Unbalanced skeleton source")
        return []
    blocks: list[dict] = []
    _walk(root, source, blocks, {"cards": 0})
    return blocks


def _local_path(url: str) -> Path | None:
    """Local file for a page URL, or None when it is not a readable file.

    QML hands over `Qt.resolvedUrl(...)` values (`file:///...`), but a raw local path
    is accepted too: `QUrl` reads a Windows path such as `D:\\x\\P.qml` as a URL with
    scheme `d`, so `toLocalFile()` alone would reject a perfectly valid file.
    QML 传入的是 `Qt.resolvedUrl(...)`(`file:///...`)，但裸本地路径同样接受: `QUrl` 会把
    形如 `D:\\x\\P.qml` 的 Windows 路径当作 scheme 为 `d` 的 URL，只用 `toLocalFile()`
    会拒绝一个完全合法的文件。
    """
    if not url:
        return None
    local = QUrl(url).toLocalFile()
    path = Path(local) if local else Path(url)
    return path if path.is_file() else None


def _parse_file(path: Path) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        debug(f"骨架页面读取失败 Skeleton page read failed: {error}")
        return []
    except UnicodeDecodeError as error:
        debug(f"骨架页面解码失败 Skeleton page decode failed: {error}")
        return []
    return infer_blocks(source)


class SkeletonSource(QObject):
    """QML-facing resolver that infers a page's skeleton from its source.

    面向 QML 的解析器：从页面源码推断其骨架结构。
    """

    @Slot(str, result="QVariant")
    def blocksFor(self, url: str) -> list:
        """Declared blocks for one page URL; cached per path. 某页面 URL 的块结构，按路径缓存。"""
        path = _local_path(url)
        if path is None:
            return []
        key = str(path)
        cached = _block_cache.get(key)
        if cached is not None:
            return cached
        blocks = _parse_file(path)
        _block_cache[key] = blocks
        return blocks

    @Slot("QVariantList")
    def warm(self, urls: list) -> None:
        """Pre-parse page URLs during window construction.

        The first ``blocksFor`` call happens on the UI thread while a lazy switch
        starts, where the per-call budget is a single frame. Parsing every page
        up front moves that cost into window construction, which is allowed to
        take longer, so the later calls only ever hit the cache.
        UI 线程上首次调用 ``blocksFor`` 发生在懒加载切换开始时, 那里单次预算只有一帧。
        在窗口构建期预先解析全部页面可把该成本前移, 之后调用只命中缓存。
        """
        if not urls:
            return
        for url in urls:
            # `pageSources` carries QUrl values, but a string is accepted too so the
            # warm-up works for hosts that build their list by hand.
            # `pageSources` 里是 QUrl 值, 但也接受字符串, 便于手工构造列表的宿主预热。
            if isinstance(url, QUrl):
                self.blocksFor(url.toString())
            elif isinstance(url, str):
                self.blocksFor(url)


_source_instance: SkeletonSource | None = None


def get_skeleton_source() -> SkeletonSource:
    """Shared skeleton source resolver. 共享骨架来源解析器。"""
    global _source_instance
    if _source_instance is None:
        _source_instance = SkeletonSource()
    return _source_instance


def warm_skeleton_source(page_sources) -> None:
    """Best-effort pre-parse of a window's pages. 窗口页面的尽力预解析。

    Never raises: a page that cannot be read simply keeps the generic skeleton.
    绝不抛错: 读不到的页面保持通用骨架即可。
    """
    try:
        get_skeleton_source().warm(list(page_sources or []))
    except (TypeError, ValueError) as error:
        debug(f"骨架预热失败 Skeleton warm-up failed: {error}")
