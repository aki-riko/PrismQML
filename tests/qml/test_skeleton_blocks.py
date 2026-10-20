# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Declared skeleton block layout contracts. 声明式骨架块布局合同。

Real-runtime evidence that a page's `pageProperties.skeleton` declaration drives the
skeleton layout, that the engine still owns every block size, and that every
unusable declaration falls back to the generic skeleton without a single warning.
以真实运行时为证: 页面 `pageProperties.skeleton` 声明驱动骨架布局, 尺寸仍由引擎掌握,
且每种不可用声明都无警告地回退到通用骨架。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
SKELETON_ENUM_SOURCE = QML_ROOT / "PrismEnums" / "Skeleton.qml"
SKELETON_BLOCK_SOURCE = (
    QML_ROOT / "controls" / "feedback" / "_internal" / "QMLPageSkeletonBlock.qml"
)
SKELETON_DISPATCH_SOURCE = (
    QML_ROOT / "controls" / "feedback" / "_internal" / "QMLPageSkeleton.qml"
)

# The frozen 18 block types and their exact values. 冻结的 18 种块类型及其精确取值。
BLOCK_TYPES = (
    ("block_title", 0),
    ("block_subtitle", 1),
    ("block_text", 2),
    ("block_textLines", 3),
    ("block_card", 4),
    ("block_buttonRow", 5),
    ("block_button", 6),
    ("block_icon", 7),
    ("block_avatar", 8),
    ("block_image", 9),
    ("block_list", 10),
    ("block_listItem", 11),
    ("block_input", 12),
    ("block_tabs", 13),
    ("block_divider", 14),
    ("block_chart", 15),
    ("block_carousel", 16),
    ("block_table", 17),
)

# Type name used by the renderer for object names. 渲染器用于对象名的类型名。
TYPE_NAMES = {value: name.replace("block_", "") for name, value in BLOCK_TYPES}

PAGE_SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root
    property var declared: []
    width: __WIDTH__
    height: __HEIGHT__

    QMLPage {
        id: page
        objectName: "probePage"
        anchors.fill: parent
        text: ""
        backgroundColor: Enums.transparent
        style: Enums.lazyLoadingStyle.style_skeleton
        skeletonBlocks: root.declared
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    """Every visual descendant in tree order. 全部可视后代, 按树序。"""
    found: list[QQuickItem] = []
    for child in item.childItems():
        found.append(child)
        found.extend(_visual_descendants(child))
    return found


def _evaluate(root: QObject, expression: str):
    qml_expression = QQmlExpression(
        QQmlEngine.contextForObject(root), root, expression
    )
    value = qml_expression.evaluate()
    assert not qml_expression.hasError(), qml_expression.error().toString()
    if isinstance(value, tuple):
        value = value[0]
    # QML returns JS arrays as QJSValue; unwrap so Python can compare them.
    # QML 把 JS 数组作为 QJSValue 返回; 解包后 Python 才能比较。
    return _variant(value)


def _variant(value):
    """Unwrap a QJSValue/QVariant so Python can compare it. 解包以便 Python 比较。"""
    return value.toVariant() if hasattr(value, "toVariant") else value


class _Scene:
    """One live skeleton scene plus its warnings. 一个活的骨架场景及其告警。"""

    def __init__(self, engine, component, root, warnings):
        self.engine = engine
        self.component = component
        self.root = root
        self.warnings = warnings

    def declare(self, expression: str) -> None:
        _evaluate(self.root, f"root.declared = {expression}")
        _pump(60)

    def page(self) -> QQuickItem:
        page = self.root.findChild(QQuickItem, "probePage")
        assert page is not None
        return page

    def blocks(self) -> list[QQuickItem]:
        return [
            item
            for item in _visual_descendants(self.page())
            if item.objectName().startswith("qmlPageSkeletonBlock-")
        ]

    def cells(self) -> list[QQuickItem]:
        """Visible Skeleton cells only. 仅可见的 Skeleton 单元。

        Card interiors are built lazily, but a card whose children are declared
        still holds an inactive default-interior subtree; counting hidden objects
        would overstate the layout.
        卡片内部结构按需构建, 但声明了子块的卡片仍持有未启用的默认内部结构子树;
        把隐藏对象计入会高估布局。
        """
        return [
            item
            for item in _visual_descendants(self.page())
            if item.objectName() == "qmlPageSkeletonBlockCell"
            and item.metaObject().className().startswith("Skeleton")
            and item.isVisible()
        ]

    def generic_objects(self) -> list[QQuickItem]:
        return [
            item
            for item in _visual_descendants(self.page())
            if item.objectName()
            in (
                "qmlPageSkeletonHeader",
                "qmlPageSkeletonRow",
                "qmlPageSkeletonCard",
            )
        ]

    def dispose(self) -> None:
        self.root.deleteLater()
        del self.component
        self.engine.deleteLater()
        _pump(1)


def _open_scene(width: int = 1280, height: int = 800) -> _Scene:
    source = (
        PAGE_SCENE.replace(b"__WIDTH__", str(width).encode("ascii"))
        .replace(b"__HEIGHT__", str(height).encode("ascii"))
    )
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:skeleton-blocks.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(50)
    return _Scene(engine, component, root, warnings)


def _measure_one(type_name: str, width: int = 1280, height: int = 800):
    """Measure one declared block by its bare type name. 按裸类型名测量单个声明块。"""
    scene = _open_scene(width, height)
    try:
        scene.declare(f"[ {{ type: Enums.skeleton.block_{type_name} }} ]")
        blocks = scene.blocks()
        assert len(blocks) == 1, [b.objectName() for b in blocks]
        block = blocks[0]
        return (
            block.objectName(),
            round(block.width(), 2),
            round(block.height(), 2),
            [
                (round(cell.width(), 2), round(cell.height(), 2))
                for cell in scene.cells()
            ],
            scene.generic_objects(),
        )
    finally:
        scene.dispose()


def test_skeleton_block_enum_values_are_frozen():
    """18 种块类型必须按冻结值注册，且既有 shape_* 保持不变。"""
    source = SKELETON_ENUM_SOURCE.read_text(encoding="utf-8")
    for name, value in BLOCK_TYPES:
        assert re.search(rf"readonly property int {name}: {value}\b", source), name
    for name, value in (
        ("shape_rect", 0),
        ("shape_circle", 1),
        ("shape_rounded", 2),
    ):
        assert re.search(rf"readonly property int {name}: {value}\b", source), name


@pytest.mark.parametrize(("name", "value"), BLOCK_TYPES, ids=[n for n, _ in BLOCK_TYPES])
def test_every_block_type_renders_a_real_sized_cell(qapp, name, value):
    """18 种块逐一真实渲染: 对象存在、宽高为正、且不触发通用回退。"""
    object_name, width, height, cells, generic = _measure_one(TYPE_NAMES[value])
    assert object_name == f"qmlPageSkeletonBlock-{TYPE_NAMES[value]}"
    assert width > 0 and height > 0, (name, width, height)
    assert cells, f"{name}: no Skeleton cell rendered"
    assert all(cell_width > 0 and cell_height > 0 for cell_width, cell_height in cells)
    # A declared page must not build generic fallback objects at all.
    # 有声明的页面完全不得创建通用回退对象。
    assert generic == [], (name, [g.objectName() for g in generic])


def test_block_shapes_match_their_semantics(qapp):
    """每种块的形状必须与语义相符，而不是千篇一律的整宽长条。"""
    # The block spans the row; the CELL is the shape. An avatar cell is a circle:
    # equal width and height, and round.
    # 块铺满整行; 形状体现在单元上。头像单元是圆: 宽高相等且为圆形。
    _, _, _, avatar_cells, _ = _measure_one("avatar")
    assert len(avatar_cells) == 1, avatar_cells
    avatar_cell_width, avatar_cell_height = avatar_cells[0]
    assert avatar_cell_width == avatar_cell_height, avatar_cells
    avatar_scene = _open_scene()
    try:
        avatar_scene.declare("[ { type: Enums.skeleton.block_avatar } ]")
        assert avatar_scene.cells()[0].property("shape") == _evaluate(
            avatar_scene.root, "Enums.skeleton.shape_circle"
        )
    finally:
        avatar_scene.dispose()

    _, _, _, icon_cells, _ = _measure_one("icon")
    assert len(icon_cells) == 1, icon_cells
    icon_cell_width, icon_cell_height = icon_cells[0]
    assert icon_cell_width == icon_cell_height, icon_cells

    # Divider is a hairline: far thinner than anything else.
    _, _, divider_height, divider_cells, _ = _measure_one("divider")
    assert divider_height <= 2, divider_height
    assert divider_cells == [(1248.0, divider_height)], divider_cells
    assert divider_cells[0][0] > divider_height * 100

    # Title is a short bar, not a full-width paragraph row: the CELL is narrow even
    # though the block container spans the row.
    # 标题是短条而非整宽段落行: 尽管块容器铺满整行, 单元本身很窄。
    _, _, title_height, title_cells, _ = _measure_one("title")
    assert title_height < 40, title_height
    assert len(title_cells) == 1, title_cells
    assert title_cells[0][0] < 1248 * 0.75, title_cells

    # Chart and image are large blocks, much taller than a text row.
    _, _, chart_height, _, _ = _measure_one("chart")
    _, _, image_height, _, _ = _measure_one("image")
    assert chart_height > 100, chart_height
    assert image_height > 100, image_height

    # Text lines repeat per declared `lines`; a list repeats per `items`.
    scene = _open_scene()
    try:
        scene.declare("[ { type: Enums.skeleton.block_textLines, lines: 5 } ]")
        assert len(scene.cells()) == 5
        scene.declare("[ { type: Enums.skeleton.block_list, items: 7 } ]")
        assert len(scene.cells()) == 7
        scene.declare("[ { type: Enums.skeleton.block_buttonRow, buttons: 3 } ]")
        assert len(scene.cells()) == 3
        scene.declare("[ { type: Enums.skeleton.block_table, columns: 5, items: 4 } ]")
        # 5 columns x 4 body rows, plus the header bar.
        assert len(scene.cells()) == 20
    finally:
        scene.dispose()


def test_carousel_lays_its_cards_out_horizontally(qapp):
    """轮播必须是横向多块，而不是纵向堆叠。"""
    scene = _open_scene()
    try:
        scene.declare(
            "[ { type: Enums.skeleton.block_carousel, cards: 3 } ]"
        )
        cells = scene.cells()
        assert len(cells) == 3, len(cells)
        # Same top edge and strictly increasing x means a real horizontal row.
        tops = {round(cell.y(), 2) for cell in cells}
        lefts = sorted(round(cell.x(), 2) for cell in cells)
        assert len(tops) == 1, tops
        assert lefts == sorted(set(lefts)) and len(set(lefts)) == 3, lefts
        assert all(cell.width() > 0 for cell in cells)
    finally:
        scene.dispose()


def test_card_contains_its_declared_children_with_padding(qapp):
    """容器块必须容纳子块并留出内边距，而不是只画一个空矩形。"""
    scene = _open_scene()
    try:
        scene.declare(
            "[ { type: Enums.skeleton.block_card, children: ["
            " { type: Enums.skeleton.block_textLines, lines: 3 },"
            " { type: Enums.skeleton.block_buttonRow, buttons: 2 } ] } ]"
        )
        blocks = scene.blocks()
        assert len(blocks) == 1
        card = blocks[0]
        surface = card.findChild(QQuickItem, "qmlPageSkeletonCardSurface")
        assert surface is not None, "card must render an outlined surface"
        assert surface.width() > 0 and surface.height() > 0
        # The card must be taller than the widest single child, i.e. it actually
        # stacks its children plus padding rather than collapsing.
        cells = scene.cells()
        assert len(cells) == 5, len(cells)
        child_total = sum(cell.height() for cell in cells)
        assert card.height() > child_total, (card.height(), child_total)
        # Every child stays inside the card's inner area.
        for cell in cells:
            assert cell.width() <= card.width()
        assert scene.generic_objects() == []
    finally:
        scene.dispose()


def test_height_override_applies_only_to_ratio_blocks(qapp):
    """`height` 只允许覆写 image/chart/carousel 的高度比例, 且仍随区域缩放。"""
    scene = _open_scene()
    try:
        # A taller declared chart must be taller than the default one.
        scene.declare("[ { type: Enums.skeleton.block_chart } ]")
        default_chart = scene.blocks()[0].height()
        scene.declare("[ { type: Enums.skeleton.block_chart, height: 0.5 } ]")
        taller_chart = scene.blocks()[0].height()
        assert taller_chart > default_chart, (taller_chart, default_chart)
        # A ratio block still scales with the area, so it is not a fixed size.
        assert scene.cells()[0].height() == taller_chart

        # `height` is meaningless for a token-sized block and must be ignored.
        scene.declare("[ { type: Enums.skeleton.block_title, height: 0.9 } ]")
        assert scene.blocks()[0].height() < 40

        # Out-of-range values are clamped, never trusted verbatim.
        scene.declare("[ { type: Enums.skeleton.block_chart, height: 5 } ]")
        assert scene.blocks()[0].height() <= 800
    finally:
        scene.dispose()


def test_count_parameters_are_clamped_to_their_bounds(qapp):
    """数量参数必须夹紧在引擎上下限内, 不得让声明撑爆骨架。"""
    scene = _open_scene()
    try:
        # Absurd counts are capped rather than honoured.
        scene.declare("[ { type: Enums.skeleton.block_textLines, lines: 9999 } ]")
        assert len(scene.cells()) == 12
        scene.declare("[ { type: Enums.skeleton.block_list, items: -5 } ]")
        assert len(scene.cells()) == 1
        scene.declare("[ { type: Enums.skeleton.block_table, columns: 999 } ]")
        header_columns = len(
            [
                item
                for item in scene.cells()
            ]
        )
        # 8 columns x 3 default rows.
        assert header_columns == 24, header_columns
        # Malformed counts fall back to the engine default.
        scene.declare("[ { type: Enums.skeleton.block_textLines, lines: 'many' } ]")
        assert len(scene.cells()) == 3
    finally:
        scene.dispose()


def test_block_sizes_follow_the_available_area(qapp):
    """同一份声明在两种可用区域下尺寸必须随之变化: 尺寸由引擎推导, 不是调用方传入。"""
    small = _measure_one("chart", 640, 480)
    large = _measure_one("chart", 1600, 1000)
    assert small[1] != large[1], (small, large)
    assert small[2] != large[2], (small, large)
    assert large[2] > small[2]

    small_title = _measure_one("title", 640, 480)
    large_title = _measure_one("title", 1600, 1000)
    assert large_title[1] > small_title[1]
    # A token-driven height is area-independent; a ratio-driven one is not.
    # 令牌驱动的高度与区域无关; 比例驱动的高度则随区域变化。
    assert large_title[2] == small_title[2]


def test_page_declaration_drives_the_layout_instead_of_the_generic_skeleton(qapp):
    """有声明时必须渲染声明布局并完全取代通用骨架。"""
    scene = _open_scene()
    try:
        scene.declare(
            "[ { type: Enums.skeleton.block_title },"
            " { type: Enums.skeleton.block_subtitle },"
            " { type: Enums.skeleton.block_card } ]"
        )
        names = [block.objectName() for block in scene.blocks()]
        assert names == [
            "qmlPageSkeletonBlock-title",
            "qmlPageSkeletonBlock-subtitle",
            "qmlPageSkeletonBlock-card",
        ]
        assert scene.generic_objects() == []
        assert scene.warnings == []
    finally:
        scene.dispose()


# ==================== Fallback paths 回退路径 ====================

FALLBACK_DECLARATIONS = (
    ("absent skeleton key", "undefined"),
    ("empty declaration", "[]"),
    ("non-array declaration", "42"),
    ("string declaration", '"title"'),
    ("unknown type", "[ { type: 99 } ]"),
    ("negative type", "[ { type: -1 } ]"),
    ("fractional type", "[ { type: 1.5 } ]"),
    ("missing type", "[ { lines: 3 } ]"),
    ("non-object entry", "[ 7 ]"),
    ("mixed known and unknown", "[ { type: Enums.skeleton.block_title }, { type: 99 } ]"),
)


@pytest.mark.parametrize(
    ("label", "expression"),
    FALLBACK_DECLARATIONS,
    ids=[label for label, _ in FALLBACK_DECLARATIONS],
)
def test_unusable_declaration_falls_back_to_the_generic_skeleton(
    qapp, label, expression
):
    """不可用声明必须回退通用骨架: 不报错、不留白、无 QML 警告。"""
    scene = _open_scene()
    try:
        scene.declare(expression)
        assert scene.blocks() == [], f"{label}: declared blocks rendered"
        generic = scene.generic_objects()
        assert generic, f"{label}: generic skeleton missing (blank screen)"
        names = {item.objectName() for item in generic}
        assert "qmlPageSkeletonHeader" in names
        assert "qmlPageSkeletonCard" in names
        rows = [item for item in generic if item.objectName() == "qmlPageSkeletonRow"]
        assert rows, f"{label}: generic rows missing"
        assert scene.warnings == [], f"{label}: {scene.warnings}"
    finally:
        scene.dispose()


def test_unknown_block_inside_a_card_does_not_break_the_card(qapp):
    """卡片内出现未知子块时, 丢弃该子块而不是让整页回退。"""
    scene = _open_scene()
    try:
        scene.declare(
            "[ { type: Enums.skeleton.block_card, children: ["
            " { type: 99 }, { type: Enums.skeleton.block_text } ] } ]"
        )
        blocks = scene.blocks()
        assert len(blocks) == 1
        assert blocks[0].objectName() == "qmlPageSkeletonBlock-card"
        # The valid child still renders; the unknown one is dropped.
        assert len(scene.cells()) == 1
        assert scene.warnings == []
    finally:
        scene.dispose()


def test_ring_style_does_not_build_any_declared_block(qapp):
    """环形模式下即使有声明也不得创建任何骨架块。"""
    source = PAGE_SCENE.replace(b"__WIDTH__", b"1280").replace(b"__HEIGHT__", b"800")
    source = source.replace(
        b"style: Enums.lazyLoadingStyle.style_skeleton",
        b"style: Enums.lazyLoadingStyle.style_ring",
    )
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:skeleton-blocks-ring.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    try:
        assert root is not None
        _evaluate(
            root,
            "root.declared = [ { type: Enums.skeleton.block_card } ]",
        )
        _pump(60)
        page = root.findChild(QQuickItem, "probePage")
        skeleton_objects = [
            item
            for item in _visual_descendants(page)
            if item.metaObject().className().startswith("Skeleton")
        ]
        assert skeleton_objects == []
        loader = page.findChild(QObject, "qmlPageSkeletonLoader")
        assert loader is not None
        assert loader.property("active") is False
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


# ==================== Delivery chain 传递链路 ====================

# A real StackedWidget fed by `pageSources` and `pageProperties`, i.e. the exact
# channel a page registers its declaration through.
# 真实 StackedWidget, 由 pageSources 与 pageProperties 供给, 即页面注册声明的确切通道。
CHAIN_SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root
    property var skeletonDeclarations: []
    width: 900
    height: 600

    StackedWidget {
        id: stack
        objectName: "chainStack"
        anchors.fill: parent
        lazyLoading: true
        lazyAnimationType: Enums.lazyAnimation.none
        lazyLoadingStyle: Enums.lazyLoadingStyle.style_skeleton
        animationType: Enums.animation.none
        pageSources: ["__PAGE0__", "__PAGE1__"]
        pageProperties: root.skeletonDeclarations
    }
}
"""


def _chain_scene(tmp_path: Path):
    page_urls = []
    for index in range(2):
        page = tmp_path / f"chain_page_{index}.qml"
        # `marker` makes the page a realistic consumer of pageProperties, so the
        # metadata filter can be proven to keep real properties intact.
        # `marker` 让页面成为 pageProperties 的真实消费者, 从而证明元数据过滤保留了
        # 真实属性。
        page.write_text(
            "import QtQuick\n"
            "Item {\n"
            '    property string marker: "unset"\n'
            f'    objectName: "chainPage{index}-" + marker\n'
            "}\n",
            encoding="utf-8",
        )
        page_urls.append(QUrl.fromLocalFile(str(page)).toString())
    source = (
        CHAIN_SCENE.replace(b"__PAGE0__", page_urls[0].encode("utf-8"))
        .replace(b"__PAGE1__", page_urls[1].encode("utf-8"))
    )
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:skeleton-chain.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(300)
    return engine, component, root, warnings


def _wait_until(predicate, timeout_ms: int = 6000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(20)
        elapsed += 20
    return predicate()


def test_page_properties_declaration_reaches_the_overlay_skeleton(qapp, tmp_path):
    """pageProperties 声明必须经真实 StackedWidget 到达覆盖层并渲染出对应块。"""
    engine, component, root, warnings = _chain_scene(tmp_path)
    try:
        stack = root.findChild(QObject, "chainStack")
        assert stack is not None
        assert _wait_until(lambda: stack.property("_displayIndex") == 0)

        # Page 1 declares a document-style layout plus a real initial property;
        # page 0 declares none.
        # 页 1 声明文档型布局并带一个真实初始属性; 页 0 无声明。
        _evaluate(
            root,
            "root.skeletonDeclarations = ["
            " {},"
            " { marker: 'kept', skeleton: ["
            "   { type: Enums.skeleton.block_title },"
            "   { type: Enums.skeleton.block_subtitle },"
            "   { type: Enums.skeleton.block_card } ] } ]",
        )
        _pump(100)

        # The engine reads the declaration from host metadata, before the target
        # page exists: that is the whole reason it lives in pageProperties.
        # 引擎在目标页存在之前就从宿主元数据读取声明: 这正是声明放在 pageProperties 的原因。
        blocks_for_target = _evaluate(root, "stack._skeletonBlocksFor(1)")
        assert len(blocks_for_target) == 3, blocks_for_target
        assert _evaluate(root, "stack._skeletonBlocksFor(0)") == []

        # Reserved metadata must not leak into the page's initial properties:
        # `pageProperties` doubles as the initial-property map, and assigning
        # `skeleton` to a page that does not declare it raises a QML error.
        # 保留元数据不得泄漏进页面初始属性: `pageProperties` 同时充当初始属性映射, 把
        # `skeleton` 赋给未声明该属性的页面会产生 QML 错误。
        initial = _evaluate(root, "stack._initialPropertiesFor(1)")
        assert "skeleton" not in initial, initial
        assert initial.get("marker") == "kept", initial
        assert _evaluate(root, "stack._initialPropertiesFor(0)") == {}

        stack.setProperty("currentIndex", 1)
        # Capture the overlay's declaration while the switch is still in flight:
        # once the reveal finishes, the helper clears its pending target and the
        # binding correctly resolves back to an empty list.
        # 在切换进行中捕获覆盖层声明: 揭幕结束后辅助器会清空待处理目标, 绑定随之正确地
        # 解析回空列表。
        observed: list = []
        elapsed = 0
        while elapsed < 6000:
            overlay = stack.findChild(QQuickItem, "lazyLoadingOverlay")
            if overlay is not None:
                declared = _variant(overlay.property("skeletonBlocks"))
                if declared:
                    observed = declared
                    break
            _pump(20)
            elapsed += 20
        assert len(observed) == 3, observed
        assert [entry["type"] for entry in observed] == [0, 1, 4]
        assert _wait_until(lambda: stack.property("_displayIndex") == 1)
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_page_without_a_declaration_still_shows_the_generic_skeleton(qapp, tmp_path):
    """未声明骨架的页面必须回退通用骨架, 不得留白。"""
    engine, component, root, warnings = _chain_scene(tmp_path)
    try:
        stack = root.findChild(QObject, "chainStack")
        assert stack is not None
        assert _wait_until(lambda: stack.property("_displayIndex") == 0)
        # Both pages lack a `skeleton` key, which is the common case.
        # 两个页面都没有 `skeleton` 键, 这是绝大多数页面的情形。
        assert _evaluate(root, "stack._skeletonBlocksFor(1)") == []
        overlay = stack.findChild(QQuickItem, "lazyLoadingOverlay")
        assert overlay is not None
        assert _variant(overlay.property("skeletonBlocks")) == []
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_declared_layout_consumes_the_public_skeleton_component():
    """渲染器必须复用公开 Skeleton 组件, 不得自造骨架矩形或硬编码几何。"""
    source = SKELETON_BLOCK_SOURCE.read_text(encoding="utf-8")
    assert "Skeleton {" in source
    assert "Rectangle {" not in source.replace("Rectangle {\n            objectName: \"qmlPageSkeletonCardSurface\"", "")
    # No caller-supplied geometry: the block receives structure and an area only.
    # 调用方不提供几何: 块只接收结构与可用区域。
    for banned in ("property real blockWidth", "property real blockHeight"):
        assert banned not in source
    # Every size must come through the layout maths or Enums tokens.
    assert "Enums.skeletonMetrics." in source
    assert "SkeletonLayout." in source

    dispatch = SKELETON_DISPATCH_SOURCE.read_text(encoding="utf-8")
    assert "SkeletonLayout.normalize(" in dispatch
    # The generic skeleton must be held in an inactive Loader when a declaration
    # exists, so the two paths never coexist.
    # 有声明时通用骨架必须持有在不激活的 Loader 中, 使两条路径永不共存。
    assert "active: !control._hasDeclaration" in dispatch
