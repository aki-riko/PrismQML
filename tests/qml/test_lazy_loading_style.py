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
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
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
    property int currentIndex: 0
    property bool _pythonPageMode: false
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
