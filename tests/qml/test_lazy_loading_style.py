# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Lazy-loading display style contracts. 懒加载展示形式合同。

Real-runtime evidence for the second lazy-loading display style (skeleton) and
for the forwarding chain that carries it from the window down to the page.
懒加载第二种展示形式（骨架屏）以及从窗口转发到页面的链路，均以真实运行时为证。
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QPointF, QTimer, QUrl
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
INTERNAL_DIR = QML_ROOT / "_internal"
INTERNAL_URL = QUrl.fromLocalFile(str(INTERNAL_DIR)).toString()

STYLE_ENUM_SOURCE = QML_ROOT / "PrismEnums" / "LazyLoadingStyle.qml"
STYLE_ENUM_QMLDIR = QML_ROOT / "PrismEnums" / "qmldir"
ENUMS_SOURCE = QML_ROOT / "Enums.qml"
SKIN_CONTEXT_SOURCE = QML_ROOT / "SkinContext.qml"
METRICS_SOURCE = QML_ROOT / "PrismEnums" / "Metrics.qml"
# Skeleton tokens live in _internal so Metrics.qml stays under its size gate; the
# public namespace path (`Enums.skeletonMetrics`) is unchanged.
# 骨架令牌放在 _internal 以保证 Metrics.qml 留在体积门禁内；公开命名空间路径
# （`Enums.skeletonMetrics`）不变。
METRICS_SKELETON_SOURCE = (
    QML_ROOT / "PrismEnums" / "_internal" / "MetricsSkeleton.qml"
)
PAGE_SOURCE = QML_ROOT / "controls" / "feedback" / "QMLPage.qml"
SKELETON_LAYOUT_SOURCE = (
    QML_ROOT / "controls" / "feedback" / "_internal" / "QMLPageSkeleton.qml"
)
PAGE_STACK_SOURCE = INTERNAL_DIR / "WindowsPageStack.qml"
STACKED_WIDGET_SOURCE = QML_ROOT / "controls" / "navigation" / "StackedWidget.qml"
LAZY_HELPER_SOURCE = (
    QML_ROOT / "controls" / "navigation" / "_internal" / "LazyLoadingHelper.qml"
)
LAZY_CONTROLLER_SOURCE = (
    QML_ROOT / "controls" / "navigation" / "_internal" / "StackedLazyController.qml"
)
WINDOW_CORE_SOURCE = QML_ROOT / "NavigationWindowCore.qml"

# Two clearly different overlay areas: the row count must follow the available
# height, which is the whole point of an engine-sized skeleton layout.
# 两个差异明显的覆盖层尺寸：行数必须随可用高度变化，这正是骨架由引擎定尺寸的意义。
SMALL_OVERLAY = (640, 480)
LARGE_OVERLAY = (1280, 800)

PAGE_SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root
    property int ringStyle: Enums.lazyLoadingStyle.style_ring
    property int skeletonStyle: Enums.lazyLoadingStyle.style_skeleton
    property int minRows: Enums.skeletonMetrics.pageRowMinCount
    property int maxRows: Enums.skeletonMetrics.pageRowMaxCount
    property int finishDuration: Enums.duration.fast
    property int normalDuration: Enums.duration.normal
    width: __WIDTH__
    height: __HEIGHT__

    function dropExitCallback() { page._completeFinish() }

    QMLPage {
        id: page
        objectName: "qmlPage"
        anchors.fill: parent
        text: "Loading page"
        backgroundColor: Enums.transparent
        style: __STYLE__
    }
}
"""

PAGE_STACK_SCENE = b"""
import QtQuick
import PrismQML
import "__INTERNAL_URL__"

Item {
    id: root
    property int ringStyle: Enums.lazyLoadingStyle.style_ring
    property int skeletonStyle: Enums.lazyLoadingStyle.style_skeleton
    property bool lazyLoading: false
    property var pageSources: []
    property var pageProperties: []
    property int currentIndex: 0
    property bool _pythonPageMode: false
    property int _pythonPendingIndex: -1
    property var _pythonLoadingOverlay: null
    property var hostValue: root
    property int lazyLoadingStyle: ringStyle

    function _handlePythonLazyCollapseFinished(index) {}
    function _beginPythonLoadingVisualExit(index) {}
    function _completePythonLoadingVisual(index) {}
    function _handlePythonLoadingOverlayReady() {}

    width: 800
    height: 600

    WindowsPageStack {
        id: pageStack
        objectName: "pageStack"
        anchors.fill: parent
        host: root.hostValue
        navAnimationEnabled: false
        overlayActive: true
        overlayText: "Loading"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene(source: bytes, url: str):
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / url)))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _page_scene(width: int, height: int, style_expression: str):
    source = (
        PAGE_SCENE.replace(b"__WIDTH__", str(width).encode("ascii"))
        .replace(b"__HEIGHT__", str(height).encode("ascii"))
        .replace(b"__STYLE__", style_expression.encode("ascii"))
    )
    return _create_scene(source, "lazy-loading-style-page.qml")


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    """Every visual descendant, in tree order. 全部可视后代，按树序。

    Repeater delegates are visual children of the Repeater's parent but are not
    parented to it as QObjects, so ``findChildren`` cannot see them; the visual
    tree is the only view that contains every skeleton block.
    Repeater 委托是 Repeater 父项的可视子项，但其 QObject 父级不是它，因此
    ``findChildren`` 看不到它们；只有可视树包含全部骨架块。
    """
    descendants: list[QQuickItem] = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _skeleton_blocks(page: QQuickItem) -> list[QQuickItem]:
    """Every Skeleton instance under the page, in the real visual tree. 页面下真实的骨架对象。"""
    return [
        child
        for child in _visual_descendants(page)
        if child.metaObject().className().startswith("Skeleton")
    ]


def _named_blocks(page: QQuickItem, object_name: str) -> list[QQuickItem]:
    return [
        child
        for child in _visual_descendants(page)
        if child.objectName() == object_name
    ]


def test_lazy_loading_style_enum_is_registered_and_isomorphic():
    """新枚举必须在 PrismEnums/qmldir、Enums 与 SkinContext 三处同构注册。"""
    enum_source = STYLE_ENUM_SOURCE.read_text(encoding="utf-8")
    assert "readonly property int style_ring: 0" in enum_source
    assert "readonly property int style_skeleton: 1" in enum_source
    assert "LazyLoadingStyle LazyLoadingStyle.qml" in STYLE_ENUM_QMLDIR.read_text(
        encoding="utf-8"
    )

    for path in (ENUMS_SOURCE, SKIN_CONTEXT_SOURCE):
        source = path.read_text(encoding="utf-8")
        assert "LazyLoadingStyle { id: _lazyLoadingStyle }" in source, path
        assert (
            "readonly property alias lazyLoadingStyle: _lazyLoadingStyle" in source
        ), path
        # Neighbouring placement: the new module must stay adjacent to LazyAnimation.
        # 相邻放置：新模块必须与 LazyAnimation 紧邻。
        assert "LazyAnimation { id: _lazyAnimation }\n    LazyLoadingStyle" in source


def test_style_forwarding_chain_is_declared_layer_by_layer():
    """转发链路逐层绑定，不新造状态。"""
    window_source = WINDOW_CORE_SOURCE.read_text(encoding="utf-8")
    assert (
        "property int lazyLoadingStyle: Enums.lazyLoadingStyle.style_ring"
        in window_source
    )

    stack_source = STACKED_WIDGET_SOURCE.read_text(encoding="utf-8")
    assert (
        "property int lazyLoadingStyle: Enums.lazyLoadingStyle.style_ring"
        in stack_source
    )
    assert '"loadingStyle": control.lazyLoadingStyle' in stack_source

    controller_source = LAZY_CONTROLLER_SOURCE.read_text(encoding="utf-8")
    assert (
        "item.loadingStyle = Qt.binding(function() { return host.lazyLoadingStyle })"
        in controller_source
    )

    helper_source = LAZY_HELPER_SOURCE.read_text(encoding="utf-8")
    assert (
        "property int loadingStyle: Enums.lazyLoadingStyle.style_ring" in helper_source
    )
    assert "style: helper.loadingStyle" in helper_source

    page_stack_source = PAGE_STACK_SOURCE.read_text(encoding="utf-8")
    assert "lazyLoadingStyle: root.host" in page_stack_source
    assert "? root.host.lazyLoadingStyle" in page_stack_source
    assert "style: root.host" in page_stack_source

    page_source = PAGE_SOURCE.read_text(encoding="utf-8")
    assert "property int style: Enums.lazyLoadingStyle.style_ring" in page_source


def _namespace_body(source: str, declaration: str) -> str:
    """Text inside the QtObject opened by ``declaration``. 该声明所开 QtObject 的内部文本。

    Brace-matched rather than substring-searched, so a token merely mentioned in a
    comment or in a neighbouring namespace cannot satisfy the assertions below.
    用花括号配对而非字符串包含，注释或相邻命名空间里提到的令牌无法蒙混过关。
    """
    assert declaration in source, declaration
    body_start = source.index(declaration) + len(declaration)
    depth = 1
    index = body_start
    while index < len(source) and depth > 0:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    assert depth == 0, f"unclosed namespace: {declaration}"
    return source[body_start:index]


def test_skeleton_layout_tokens_land_in_the_existing_namespace():
    """新增令牌必须加在既有 skeletonMetrics 内，不新建度量命名空间。

    骨架整组令牌已按仓库既有范式抽到 `_internal/MetricsSkeleton.qml`（Metrics.qml
    因此回到 700 行门禁内），但**命名空间没有变**：入口仍以
    `readonly property QtObject skeletonMetrics: MetricsInternal.MetricsSkeleton {}`
    实例化同一个 `Enums.skeletonMetrics`。这里同时锁住两件事：入口确实是抽出去的
    实例化而非又内联了一个 QtObject，且 8 个新令牌落在该命名空间体内。
    """
    metrics = METRICS_SOURCE.read_text(encoding="utf-8")
    # The entry must delegate, not re-inline the group (no second namespace).
    # 入口必须委派，不得重新内联该组（不产生第二个命名空间）。
    delegation = (
        "readonly property QtObject skeletonMetrics: "
        "MetricsInternal.MetricsSkeleton {}"
    )
    assert delegation in metrics
    assert "readonly property QtObject skeletonMetrics: QtObject {" not in metrics
    assert "MetricsInternal.MetricsSkeleton {" not in metrics.replace(delegation, "")

    namespace_body = _namespace_body(
        METRICS_SKELETON_SOURCE.read_text(encoding="utf-8"), "QtObject {"
    )

    for token, token_type in (
        ("pageHeaderHeight", "int"),
        ("pageHeaderWidthRatio", "real"),
        ("pageRowHeight", "int"),
        ("pageRowLongRatio", "real"),
        ("pageRowShortRatio", "real"),
        ("pageRowMinCount", "int"),
        ("pageRowMaxCount", "int"),
        ("pageCardHeight", "int"),
    ):
        assert f"readonly property {token_type} {token}:" in namespace_body, token

    # The pre-existing ten tokens must survive the move with their names intact.
    # 既有十个令牌必须随搬家保留原名。
    for token in (
        "rectWidth",
        "rectHeight",
        "circleSize",
        "shimmerWidthRatio",
        "shimmerDurationMs",
        "shimmerPauseMs",
        "baseAlphaLight",
        "baseAlphaDark",
        "shimmerAlphaLight",
        "shimmerAlphaDark",
    ):
        assert re.search(rf"readonly property \w+ {token}:", namespace_body), token

    layout_source = SKELETON_LAYOUT_SOURCE.read_text(encoding="utf-8")
    # The layout must consume the shared Skeleton component, not private rectangles.
    # 布局必须复用公开 Skeleton 组件，不得自造骨架矩形。
    assert "Skeleton {" in layout_source
    assert "Rectangle {" not in layout_source
    # No caller-supplied geometry: only `loading` may cross the boundary.
    assert "property bool loading: true" in layout_source
    assert "required property" not in layout_source
    for banned in ("width: 1", "height: 1", "spacing: 8", "spacing: 16"):
        assert banned not in layout_source, banned


# Every skeleton token with its exact value. Ten pre-existing consumers
# (Skeleton.qml, SkinContext) read these, so a move must not change any value.
# 全部骨架令牌及其精确取值。既有十个消费方（Skeleton.qml、SkinContext）读取它们，
# 因此搬家不得改变任何取值。
SKELETON_TOKEN_VALUES = (
    ("rectWidth", 200),
    ("rectHeight", 16),
    ("circleSize", 48),
    ("shimmerWidthRatio", 0.5),
    ("shimmerDurationMs", 1500),
    ("shimmerPauseMs", 500),
    ("baseAlphaLight", 0.06),
    ("baseAlphaDark", 0.08),
    ("shimmerAlphaLight", 0.04),
    ("shimmerAlphaDark", 0.12),
    ("pageHeaderHeight", 24),
    ("pageHeaderWidthRatio", 0.4),
    ("pageRowHeight", 16),
    ("pageRowLongRatio", 0.9),
    ("pageRowShortRatio", 0.6),
    ("pageRowMinCount", 2),
    ("pageRowMaxCount", 16),
    ("pageCardHeight", 72),
)


def test_skeleton_metrics_resolve_at_runtime_after_the_move(qapp):
    """`Enums.skeletonMetrics` 的 18 个令牌必须在真实运行时按原值解析。

    仅检查源码文本无法发现损坏的 _internal 导入或不可实例化的 QtObject；这里通过真实
    QQmlEngine 逐名读取每个令牌，确认命名空间仍然存在且取值与抽取前一致。
    """
    token_reads = ",\n".join(
        f'        "{name}": Enums.skeletonMetrics.{name}'
        for name, _ in SKELETON_TOKEN_VALUES
    )
    source = (
        "import QtQuick\n"
        "import PrismQML\n"
        "QtObject {\n"
        "    readonly property bool namespacePresent:\n"
        "        Enums.skeletonMetrics !== null && Enums.skeletonMetrics !== undefined\n"
        "    readonly property var values: ({\n"
        f"{token_reads}\n"
        "    })\n"
        "}\n"
    ).encode("utf-8")

    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:skeleton-metrics-runtime.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        assert root.property("namespacePresent") is True, (
            "Enums.skeletonMetrics must stay reachable after the _internal move"
        )
        values = root.property("values")
        values = values.toVariant() if hasattr(values, "toVariant") else values
        assert sorted(values) == sorted(name for name, _ in SKELETON_TOKEN_VALUES)
        for name, expected in SKELETON_TOKEN_VALUES:
            actual = values[name]
            assert actual is not None, name
            if isinstance(expected, float):
                assert actual == pytest.approx(expected), name
            else:
                assert int(actual) == expected, (name, actual, expected)
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


@pytest.mark.parametrize("style_expression", ["root.ringStyle", "root.skeletonStyle"])
def test_page_geometry_stays_inside_the_overlay_bounds(qapp, style_expression):
    """两种模式下所有可见块都必须落在覆盖层边界内。"""
    width, height = LARGE_OVERLAY
    engine, component, root, warnings = _page_scene(width, height, style_expression)
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        assert page is not None
        assert page.width() == width and page.height() == height

        blocks = _skeleton_blocks(page)
        if style_expression == "root.ringStyle":
            assert blocks == []
            ring = page.findChild(QQuickItem, "qmlPageProgressRing")
            assert ring is not None
            assert ring.x() >= 0 and ring.y() >= 0
            assert ring.x() + ring.width() <= width
            assert ring.y() + ring.height() <= height
        else:
            assert blocks
            for block in blocks:
                top_left = block.mapToItem(page, QPointF(0, 0))
                assert top_left.x() >= 0, block.objectName()
                assert top_left.y() >= 0, block.objectName()
                assert top_left.x() + block.width() <= width, block.objectName()
                assert top_left.y() + block.height() <= height, block.objectName()
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_ring_mode_creates_no_skeleton_object(qapp):
    """默认 ring 路径不得创建任何 Skeleton 对象（零新增对象）。"""
    engine, component, root, warnings = _page_scene(*LARGE_OVERLAY, "root.ringStyle")
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        assert page is not None
        loader = page.findChild(QObject, "qmlPageSkeletonLoader")
        assert loader is not None
        assert loader.property("active") is False
        assert loader.property("item") is None
        assert _skeleton_blocks(page) == []
        # The ring branch is untouched and fully laid out.
        assert page.findChild(QQuickItem, "qmlPageContent") is not None
        assert page.findChild(QQuickItem, "qmlPageProgressRing") is not None
        assert page.findChild(QQuickItem, "qmlPageLabel") is not None
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_ring_mode_keeps_the_wait_indicator_object_set_unchanged(qapp):
    """ring 模式的等待指示对象集合与动画集合必须与改动前逐项一致。

    骨架 Loader 是默认路径唯一新增的对象；它的子树在 ring 模式下不得存在，且它自身
    不激活、不绘制。等待指示本体的可视项数量、几何、动画数量与时长都必须保持原值。
    这些数值由同一棵 QMLPage 在原始 HEAD 树与工作树上各跑一次真实运行时探针实测得到
    （见 tests/qml/test_lazy_loading_style.py 的 ring 对照断言），两棵树逐项相同。
    """
    engine, component, root, warnings = _page_scene(*LARGE_OVERLAY, "root.ringStyle")
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        assert page is not None
        # Park the indicator so the ring visual branch is deterministic.
        # 停驻指示器，使环形可视分支确定。
        page.setProperty("running", False)
        _pump(60)

        # The ring wait indicator itself: the pre-existing item set, unchanged.
        # 等待指示本体：与改动前相同的可视项集合。
        indicator_items = [
            item
            for item in _visual_descendants(page)
            if item.objectName() != "qmlPageSkeletonLoader"
        ]
        assert len(indicator_items) == 8
        names = [item.objectName() for item in indicator_items]
        assert names.count("qmlPageContent") == 1
        assert names.count("qmlPageProgressRing") == 1
        assert names.count("qmlPageLabel") == 1
        assert "progressRingCanvas" in names

        # Animation objects and their timings must not have moved either.
        # 动画对象及其时间参数同样不得变化。
        animations = [
            child
            for child in page.findChildren(QObject)
            if "Animation" in child.metaObject().className()
        ]
        assert len(animations) == 6
        durations = sorted(
            animation.property("duration")
            for animation in animations
            if animation.metaObject().indexOfProperty("duration") >= 0
        )
        assert durations == [100, 100, 600, 600]

        # The ring keeps its exact geometry and the original exit timing.
        # 环形保持精确几何与原有退场时序。
        ring = page.findChild(QQuickItem, "qmlPageProgressRing")
        content = page.findChild(QQuickItem, "qmlPageContent")
        assert ring.width() == ring.height()
        assert ring.x() + ring.width() / 2 == pytest.approx(
            content.width() / 2, abs=0.5
        )
        assert page.findChild(QObject, "qmlPageFinishGuard").property(
            "interval"
        ) == root.property("finishDuration") + root.property("normalDuration")
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_skeleton_mode_creates_blocks_from_the_public_skeleton_component(qapp):
    """skeleton 模式必须存在 Skeleton 对象，且由公开组件构成。"""
    engine, component, root, warnings = _page_scene(
        *LARGE_OVERLAY, "root.skeletonStyle"
    )
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        loader = page.findChild(QObject, "qmlPageSkeletonLoader")
        assert loader is not None
        assert loader.property("active") is True
        assert loader.property("item") is not None

        assert _named_blocks(page, "qmlPageSkeletonHeader")
        assert _named_blocks(page, "qmlPageSkeletonCard")
        rows = _named_blocks(page, "qmlPageSkeletonRow")
        assert rows

        classes = {block.metaObject().className() for block in _skeleton_blocks(page)}
        assert classes and all(name.startswith("Skeleton") for name in classes)
        # Header + rows + card, nothing else.
        assert len(_skeleton_blocks(page)) == len(rows) + 2
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_skeleton_row_count_follows_the_available_area(qapp):
    """引擎按可用区域自行决定骨架块数量：两种 overlay 尺寸下真实计数不同。"""
    measurements = {}
    for width, height in (SMALL_OVERLAY, LARGE_OVERLAY):
        engine, component, root, warnings = _page_scene(
            width, height, "root.skeletonStyle"
        )
        try:
            page = root.findChild(QQuickItem, "qmlPage")
            assert page is not None
            rows = _named_blocks(page, "qmlPageSkeletonRow")
            blocks = _skeleton_blocks(page)
            assert len(blocks) == len(rows) + 2
            assert root.property("minRows") <= len(rows) <= root.property("maxRows")

            geometry = []
            for row in rows:
                top_left = row.mapToItem(page, QPointF(0, 0))
                geometry.append(
                    (
                        round(top_left.x(), 2),
                        round(top_left.y(), 2),
                        round(row.width(), 2),
                        round(row.height(), 2),
                    )
                )
            measurements[(width, height)] = (len(rows), len(blocks), geometry)
            assert warnings == []
        finally:
            root.deleteLater()
            del component
            engine.deleteLater()
            _pump(1)

    small_rows, small_blocks, small_geometry = measurements[SMALL_OVERLAY]
    large_rows, large_blocks, large_geometry = measurements[LARGE_OVERLAY]
    # The engine, not the caller, sized the skeleton: more area buys more rows.
    # 尺寸由引擎而非调用方决定：可用区域更大就得到更多行。
    assert large_rows > small_rows
    assert large_blocks > small_blocks
    # Long/short alternation proves the per-position width ratios are applied.
    # 长短交替证明按位置取宽度的比例确实生效。
    assert small_geometry[0][2] > small_geometry[1][2]
    assert small_geometry[2][2] > small_geometry[3][2]
    assert small_geometry[0][3] == small_geometry[1][3]
    print(
        "SKELETON_GEOMETRY",
        {
            f"{width}x{height}": {
                "rows": rows,
                "blocks": blocks,
                "geometry": geometry,
            }
            for (width, height), (rows, blocks, geometry) in measurements.items()
        },
    )


def test_skeleton_exit_fades_and_resets_like_the_ring(qapp):
    """骨架模式的 start()/finish() 与环形模式语义一致，Loader 复位为 1。"""
    engine, component, root, warnings = _page_scene(
        *LARGE_OVERLAY, "root.skeletonStyle"
    )
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        loader = page.findChild(QObject, "qmlPageSkeletonLoader")
        assert page is not None and loader is not None
        assert loader.property("opacity") == pytest.approx(1)
        assert loader.property("scale") == pytest.approx(1)
        assert page.property("visible") is True
        assert page.property("running") is True

        rows = _named_blocks(page, "qmlPageSkeletonRow")
        assert rows and all(row.property("visible") is True for row in rows)

        finished: list[bool] = []
        page.finished.connect(lambda: finished.append(True))
        assert QMetaObject.invokeMethod(page, "finish")
        assert page.property("finishing") is True
        assert page.property("running") is False
        _pump(root.property("finishDuration") // 2)
        # Mid-exit the skeleton is fading, not blinking away.
        # 退场中途骨架是在淡出，不是瞬间消失。
        assert 0 < loader.property("opacity") < 1
        assert loader.property("scale") < 1
        assert all(row.property("visible") is True for row in rows)

        assert _wait_until(lambda: page.property("visible") is False)
        assert finished == [True]
        assert loader.property("opacity") == pytest.approx(1)
        assert loader.property("scale") == pytest.approx(1)

        # A second finish on a hidden page must stay idempotent.
        # 已隐藏页面的第二次 finish 必须保持幂等。
        assert QMetaObject.invokeMethod(page, "finish")
        assert finished == [True]

        assert QMetaObject.invokeMethod(page, "start")
        assert page.property("visible") is True
        assert page.property("running") is True
        assert loader.property("opacity") == pytest.approx(1)
        assert loader.property("scale") == pytest.approx(1)
        assert _skeleton_blocks(page)
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_ring_mode_exit_still_resets_the_content_column(qapp):
    """环形模式退场语义逐条不变（对照组）。"""
    engine, component, root, warnings = _page_scene(*LARGE_OVERLAY, "root.ringStyle")
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        content = page.findChild(QQuickItem, "qmlPageContent")
        assert page is not None and content is not None

        finished: list[bool] = []
        page.finished.connect(lambda: finished.append(True))
        assert QMetaObject.invokeMethod(page, "finish")
        _pump(root.property("finishDuration") // 2)
        assert 0 < content.property("opacity") < 1
        assert content.property("scale") < 1
        assert _wait_until(lambda: page.property("visible") is False)
        assert finished == [True]
        assert content.property("opacity") == pytest.approx(1)
        assert content.property("scale") == pytest.approx(1)
        assert _skeleton_blocks(page) == []
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def _stacked_widget(page_stack: QQuickItem) -> QObject | None:
    """The StackedWidget inside a WindowsPageStack. WindowsPageStack 内的 StackedWidget。

    The `stackAlias` property returns an unregistered QML type that PySide cannot
    convert, so the widget is located through the object tree instead.
    `stackAlias` 返回未注册的 QML 类型，PySide 无法转换，因此改为在对象树中定位。
    """
    for child in page_stack.findChildren(QObject):
        if child.metaObject().className().startswith("StackedWidget"):
            return child
    return None


def test_page_stack_forwards_the_declared_skeleton_to_the_overlay(qapp):
    """Python 宿主路径: WindowsPageStack 必须把 pageProperties 声明转发到 overlay。"""
    source = PAGE_STACK_SCENE.replace(
        b"__INTERNAL_URL__", INTERNAL_URL.encode("utf-8")
    )
    engine, component, root, warnings = _create_scene(
        source, "lazy-loading-style-page-stack-skeleton-blocks.qml"
    )
    try:
        page_stack = root.findChild(QQuickItem, "pageStack")
        assert page_stack is not None
        stack = _stacked_widget(page_stack)
        loader = page_stack.findChild(QObject, "loadingOverlayLoader")
        assert stack is not None and loader is not None
        assert root.property("skeletonStyle") == 1
        root.setProperty("lazyLoadingStyle", root.property("skeletonStyle"))
        _pump()

        # No declaration: the overlay falls back to the generic skeleton.
        overlay = loader.property("item")
        fallback = overlay.property("skeletonBlocks")
        fallback = (
            fallback.toVariant() if hasattr(fallback, "toVariant") else fallback
        )
        assert fallback in (None, []), fallback
        assert _named_blocks(overlay, "qmlPageSkeletonRow")

        # A declaration on the awaited page must reach the overlay's QMLPage, which
        # is the only way the Python host path can render a matching skeleton.
        # 被等待页面的声明必须到达 overlay 的 QMLPage, 这是 Python 宿主路径渲染匹配骨架的
        # 唯一途径。
        root.setProperty("currentIndex", 1)
        root.setProperty("_pythonPendingIndex", 1)
        root.setProperty(
            "pageProperties",
            [
                {},
                {
                    "skeleton": [
                        {"type": 0},
                        {"type": 1},
                        {"type": 4},
                    ]
                },
            ],
        )
        _pump(50)
        overlay = loader.property("item")
        declared = overlay.property("skeletonBlocks")
        declared = (
            declared.toVariant() if hasattr(declared, "toVariant") else declared
        )
        assert declared is not None and len(declared) == 3, declared
        assert [entry["type"] for entry in declared] == [0, 1, 4]
        # The declared layout replaces the generic one in the overlay too.
        # 声明布局同样取代 overlay 中的通用布局。
        assert not _named_blocks(overlay, "qmlPageSkeletonRow")
        assert _named_blocks(overlay, "qmlPageSkeletonBlock-title")
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_page_stack_forwards_the_style_to_stack_and_overlay(qapp):
    """WindowsPageStack 必须把宿主样式同时传给 StackedWidget 与 overlay 的 QMLPage。"""
    source = PAGE_STACK_SCENE.replace(
        b"__INTERNAL_URL__", INTERNAL_URL.encode("utf-8")
    )
    engine, component, root, warnings = _create_scene(
        source, "lazy-loading-style-page-stack.qml"
    )
    try:
        page_stack = root.findChild(QQuickItem, "pageStack")
        assert page_stack is not None
        stack = _stacked_widget(page_stack)
        loader = page_stack.findChild(QObject, "loadingOverlayLoader")
        assert stack is not None and loader is not None

        # Default: ring style reaches both consumers.
        assert root.property("ringStyle") == 0
        assert root.property("skeletonStyle") == 1
        assert stack.property("lazyLoadingStyle") == root.property("ringStyle")
        overlay = loader.property("item")
        assert overlay is not None
        assert overlay.property("style") == root.property("ringStyle")
        assert (
            loader.property("item")
            .findChild(QObject, "qmlPageSkeletonLoader")
            .property("active")
            is False
        )

        root.setProperty("lazyLoadingStyle", root.property("skeletonStyle"))
        _pump()
        assert stack.property("lazyLoadingStyle") == root.property("skeletonStyle")
        overlay = loader.property("item")
        assert overlay.property("style") == root.property("skeletonStyle")
        assert overlay.findChild(QObject, "qmlPageSkeletonLoader").property(
            "active"
        ) is True
        assert _named_blocks(overlay, "qmlPageSkeletonRow")
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_page_stack_falls_back_to_ring_without_a_host(qapp):
    """host 为 null 时转发链路必须退回默认 ring，不得抛错。"""
    source = PAGE_STACK_SCENE.replace(
        b"__INTERNAL_URL__", INTERNAL_URL.encode("utf-8")
    ).replace(b"property var hostValue: root", b"property var hostValue: null")
    engine, component, root, warnings = _create_scene(
        source, "lazy-loading-style-null-host.qml"
    )
    try:
        page_stack = root.findChild(QQuickItem, "pageStack")
        assert page_stack is not None
        stack = _stacked_widget(page_stack)
        loader = page_stack.findChild(QObject, "loadingOverlayLoader")
        assert stack is not None and loader is not None
        assert stack.property("lazyLoadingStyle") == root.property("ringStyle")
        # The host is null, so the skeleton style cannot be requested; the overlay
        # must still resolve to ring instead of raising a TypeError.
        # 宿主为 null，因此不可能请求骨架样式；覆盖层仍必须解析为 ring 而不是抛 TypeError。
        assert loader.property("item").property("style") == root.property("ringStyle")
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


# ==================== Skeleton style must not run the lazy circle ====================
# 骨架屏样式不得运行懒加载圆圈

# A real lazy switch: `lazyLoading` on with URL page sources, so the switch goes
# through LazyLoadingHelper -> PageTransition exactly like a real host.
# 真实懒加载切换: 开启 lazyLoading 并使用 URL 页面源, 因此切换与真实宿主一样走
# LazyLoadingHelper -> PageTransition。
LAZY_SWITCH_SCENE = b"""
import QtQuick
import PrismQML

Window {
    id: shell
    objectName: "lazySwitchShell"
    width: 640
    height: 400
    visible: true
    color: "#101010"

    StackedWidget {
        id: stack
        objectName: "lazySwitchStack"
        anchors.fill: parent
        lazyLoading: true
        lazyAnimationType: Enums.lazyAnimation.lazy_circle
        lazyLoadingStyle: __STYLE__
        animationType: Enums.animation.pop
        animationOrigin: Enums.animation.origin_bottom
        animationDuration: __DURATION__
        pageSources: ["__PAGE0__", "__PAGE1__"]
    }
}
"""


def _lazy_switch_scene(tmp_path: Path, style_expression: str, duration_ms: int = 200):
    tmp_path.mkdir(parents=True, exist_ok=True)
    page_urls = []
    for index in range(2):
        page = tmp_path / f"lazy_switch_page_{index}.qml"
        page.write_text(
            "import QtQuick\n"
            f'Rectangle {{ objectName: "lazySwitchPage{index}"; color: "#123456" }}\n',
            encoding="utf-8",
        )
        page_urls.append(QUrl.fromLocalFile(str(page)).toString())
    source = (
        LAZY_SWITCH_SCENE.replace(b"__STYLE__", style_expression.encode("ascii"))
        .replace(b"__DURATION__", str(duration_ms).encode("ascii"))
        .replace(b"__PAGE0__", page_urls[0].encode("utf-8"))
        .replace(b"__PAGE1__", page_urls[1].encode("utf-8"))
    )
    return _create_scene(source, "lazy-loading-circle-style.qml")


def _lazy_switch_fixture(tmp_path: Path, style_expression: str):
    engine, component, root, warnings = _lazy_switch_scene(tmp_path, style_expression)
    stack = root.findChild(QObject, "lazySwitchStack")
    assert stack is not None
    transition = stack.findChild(QObject, "lazyPageCircleTransition")
    assert transition is not None
    return engine, component, root, warnings, stack, transition


def _drive_lazy_switch(stack: QObject, transition: QObject) -> tuple:
    """Run one lazy switch, sampling the circle on every turn. 执行一次懒加载切换并逐回合采样。"""
    samples: list[tuple] = []
    events: list[str] = []
    stack.animationStarted.connect(lambda: events.append("animationStarted"))
    stack.animationFinished.connect(lambda: events.append("animationFinished"))
    # `currentChanged` is the public contract page managers listen to; it must keep
    # firing when the reveal moves from the circle to the native animation.
    # `currentChanged` 是页面管理器监听的公开合同; 揭幕从圆圈改到原生动画后它必须继续触发。
    stack.currentChanged.connect(lambda index: events.append(f"currentChanged({index})"))

    def sample() -> None:
        samples.append(
            (
                int(transition.property("animationType")),
                bool(transition.property("running")),
                bool(transition.property("active")),
            )
        )

    sample()
    assert stack.property("_displayIndex") == 0
    stack.setProperty("currentIndex", 1)

    settled = False
    elapsed = 0
    while elapsed < 8000:
        sample()
        if (
            stack.property("_displayIndex") == 1
            and not bool(stack.property("busy"))
        ):
            settled = True
            break
        _pump(15)
        elapsed += 15
    for _ in range(30):
        sample()
        _pump(15)
    sample()
    return samples, events, settled


def test_skeleton_style_never_runs_the_lazy_circle_transition(qapp, tmp_path):
    """骨架屏模式: 圆圈过渡必须完全不参与, 揭幕改走 StackedWidget 原生动画。

    用户反馈骨架屏与懒加载圆圈"一起加载了"。这里用真实懒加载切换逐回合采样
    `pageCircleTransition` 的 animationType/running/active, 证明圆圈在该样式下
    不仅类型为 none, 而且从未 running/active; 同时原生动画信号确实被触发。
    """
    engine, component, root, warnings, stack, transition = _lazy_switch_fixture(
        tmp_path, "Enums.lazyLoadingStyle.style_skeleton"
    )
    try:
        samples, events, settled = _drive_lazy_switch(stack, transition)

        # (a) animationType is none for the whole switch and the circle never ran.
        assert {sample[0] for sample in samples} == {0}, sorted(
            {sample[0] for sample in samples}
        )
        assert not any(sample[1] for sample in samples), "circle ran in skeleton mode"
        assert not any(sample[2] for sample in samples), "circle active in skeleton mode"

        # (b) the reveal really is the native StackedWidget animation.
        assert settled, "skeleton lazy switch did not settle"
        assert "animationStarted" in events
        assert "animationFinished" in events
        # The public page-change contract must survive the switch to the native
        # reveal; page managers depend on it.
        # 公开的换页合同必须在改用原生揭幕后继续成立; 页面管理器依赖它。
        assert "currentChanged(1)" in events, events
        assert stack.property("_displayIndex") == 1

        # (d) the skeleton itself must still be built: killing the circle must not
        # kill the skeleton blocks.
        # (d) 骨架本身仍必须创建: 砍掉圆圈不能连骨架一起砍掉。
        overlay = stack.findChild(QObject, "lazyLoadingOverlay")
        assert overlay is not None
        assert _skeleton_blocks(overlay), "skeleton blocks missing in skeleton mode"
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_ring_style_keeps_the_lazy_circle_transition(qapp, tmp_path):
    """环形模式: 圆圈类型与 running/active 行为必须逐项不变。"""
    engine, component, root, warnings, stack, transition = _lazy_switch_fixture(
        tmp_path, "Enums.lazyLoadingStyle.style_ring"
    )
    try:
        samples, _events, settled = _drive_lazy_switch(stack, transition)

        # (c) ring keeps the circle type and really animates it.
        assert {sample[0] for sample in samples} == {7}, sorted(
            {sample[0] for sample in samples}
        )
        assert any(sample[1] for sample in samples), "ring circle never ran"
        assert any(sample[2] for sample in samples), "ring circle never became active"
        assert settled
        assert stack.property("_displayIndex") == 1
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_ring_and_skeleton_differ_only_in_the_circle(qapp, tmp_path):
    """同一场景下两种样式的差异必须且只能是圆圈过渡本身。

    环形跑圆圈、骨架屏跑原生动画; 两者的动画类型互斥, 且骨架屏下圆圈始终静止。
    这条防止"砍动画"误伤环形路径, 也防止骨架屏偷偷仍然跑圆圈。
    """
    ring_engine, ring_component, ring_root, _rw, ring_stack, ring_transition = (
        _lazy_switch_fixture(tmp_path / "ring", "Enums.lazyLoadingStyle.style_ring")
    )
    skel_engine, skel_component, skel_root, _sw, skel_stack, skel_transition = (
        _lazy_switch_fixture(
            tmp_path / "skeleton", "Enums.lazyLoadingStyle.style_skeleton"
        )
    )
    try:
        ring_samples, _re, ring_settled = _drive_lazy_switch(
            ring_stack, ring_transition
        )
        skel_samples, _se, skel_settled = _drive_lazy_switch(
            skel_stack, skel_transition
        )

        assert ring_settled and skel_settled
        assert {s[0] for s in ring_samples} == {7}
        assert {s[0] for s in skel_samples} == {0}
        assert any(s[1] for s in ring_samples)
        assert not any(s[1] for s in skel_samples)
        # Both styles must reach the same settled display index.
        assert ring_stack.property("_displayIndex") == skel_stack.property(
            "_displayIndex"
        )
    finally:
        for root, component, engine in (
            (ring_root, ring_component, ring_engine),
            (skel_root, skel_component, skel_engine),
        ):
            root.deleteLater()
            del component
            engine.deleteLater()
        _pump(1)


def _evaluate(root: QObject, expression: str):
    qml_expression = QQmlExpression(
        QQmlEngine.contextForObject(root), root, expression
    )
    value = qml_expression.evaluate()
    assert not qml_expression.hasError(), qml_expression.error().toString()
    return value[0] if isinstance(value, tuple) else value


def _drive_python_lazy_switch(root: QObject, stack: QObject, transition: QObject):
    """Python host path: complete the handshake and sample the circle.

    Python 宿主路径: 完成握手并采样圆圈。

    Gallery uses the pure QML path, but the Python host path must keep working too:
    the Python loading pipeline only finishes on `pythonLazyTransitionFinished`,
    which PageTransition emits from expandFinished. Dropping expand() outright
    would hang it, so this locks the handshake end to end.
    Gallery 使用纯 QML 路径, 但 Python 宿主路径也必须继续可用: Python 加载管线只在
    PageTransition 从 expandFinished 发出的 `pythonLazyTransitionFinished` 上收尾。
    直接去掉 expand() 会把它挂死, 因此这里端到端锁定该握手。
    """
    samples: list[tuple] = []
    events: list[str] = []
    stack.pythonLazyExpansionStarted.connect(
        lambda index: events.append(f"pythonLazyExpansionStarted({index})")
    )
    stack.pythonLazyTransitionFinished.connect(
        lambda index: events.append(f"pythonLazyTransitionFinished({index})")
    )
    stack.animationStarted.connect(lambda: events.append("animationStarted"))
    stack.animationFinished.connect(lambda: events.append("animationFinished"))

    def sample() -> None:
        samples.append(
            (
                int(transition.property("animationType")),
                bool(transition.property("running")),
                bool(transition.property("active")),
            )
        )

    sample()
    # The target must not be ready when currentIndex moves, or the lifecycle would
    # start a native animation and bypass the handshake under test.
    # currentIndex 变化时目标页必须尚未就绪, 否则生命周期会启动原生动画并绕过被测握手。
    stack.setProperty("_pythonPageMode", True)
    stack.setProperty("currentIndex", 1)
    _pump(30)
    assert stack.property("_displayIndex") == 0, (
        "python path precondition: lifecycle must not reveal before the handshake"
    )
    _evaluate(root, "stack._markPythonPageReady(1)")
    stack.setProperty("_pythonLazyTransitionTargetIndex", 1)
    stack.setProperty("_pythonLazyRevealRequested", True)
    started = _evaluate(root, "stack._completePythonLazySwitch(1)")

    settled = False
    elapsed = 0
    while elapsed < 8000:
        sample()
        if any(event.startswith("pythonLazyTransitionFinished") for event in events):
            settled = True
            break
        _pump(15)
        elapsed += 15
    for _ in range(20):
        sample()
        _pump(10)
    sample()
    return started, samples, events, settled


def test_python_path_skeleton_disables_the_circle_and_still_completes(qapp, tmp_path):
    """Python 宿主路径在骨架屏样式下也必须禁用圆圈且仍然收尾。"""
    engine, component, root, warnings, stack, transition = _lazy_switch_fixture(
        tmp_path, "Enums.lazyLoadingStyle.style_skeleton"
    )
    try:
        started, samples, events, settled = _drive_python_lazy_switch(
            root, stack, transition
        )
        assert started, "_completePythonLazySwitch refused the handshake"
        assert {sample[0] for sample in samples} == {0}
        assert not any(sample[1] for sample in samples), "circle ran in skeleton mode"
        assert not any(sample[2] for sample in samples), "circle active in skeleton mode"
        # The Python pipeline must still be told the transition finished, otherwise
        # pythonPageReady never fires and the host stays loading forever.
        # 仍必须告知 Python 管线过渡已完成, 否则 pythonPageReady 不会触发, 宿主会永久 loading。
        assert settled, "pythonLazyTransitionFinished never fired"
        assert "pythonLazyExpansionStarted(1)" in events
        assert "pythonLazyTransitionFinished(1)" in events
        assert "animationStarted" in events
        assert stack.property("_displayIndex") == 1
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_python_path_ring_still_runs_the_circle(qapp, tmp_path):
    """Python 宿主路径在环形样式下的圆圈行为必须不变。"""
    engine, component, root, warnings, stack, transition = _lazy_switch_fixture(
        tmp_path, "Enums.lazyLoadingStyle.style_ring"
    )
    try:
        started, samples, events, settled = _drive_python_lazy_switch(
            root, stack, transition
        )
        assert started
        assert {sample[0] for sample in samples} == {7}
        assert any(sample[1] for sample in samples), "ring circle never ran"
        assert any(sample[2] for sample in samples), "ring circle never became active"
        assert settled, "pythonLazyTransitionFinished never fired"
        assert "pythonLazyExpansionStarted(1)" in events
        assert stack.property("_displayIndex") == 1
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)
