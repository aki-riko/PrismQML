# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery vertical-navigation coverage. 画廊垂直导航覆盖回归。"""

import re
import time
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]
_PAGE = _ROOT / "examples" / "pages" / "NavigationPage.qml"
# The vertical-navigation card was extracted to keep the page inside its line budget,
# so implementation gates follow the real owner while the page keeps the reference.
# 垂直导航卡片已抽出以保持页面行数预算, 实现类门禁跟着真实所有者, 页面只保留引用。
_SHOWCASE = _ROOT / "examples" / "pages" / "_internal" / "NavigationPanelShowcase.qml"

# A host window is needed to deliver real mouse events to the Gallery page.
# 需要宿主窗口才能向画廊页面投递真实鼠标事件。
_GALLERY_HOST_SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: host
    objectName: "galleryHost"

    // The demo keeps a single NavigationView and switches its display mode at
    // runtime, so the pane is found by objectName instead of by mode.
    // 示例只保留一个 NavigationView 并在运行时切换显示模式, 因此用 objectName 定位。
    readonly property int compactPaneMode: Enums.navigation.pane_left_compact
    readonly property int expandedPaneMode: Enums.navigation.pane_left
    readonly property int autoPaneMode: Enums.navigation.pane_auto
    // Menu-button geometry, so the test can click the real affordance
    // 菜单按钮几何, 供测试点击真实控件
    readonly property int panePaddingH: Enums.controlSize.navPanelPaddingH
    readonly property int panePaddingV: Enums.controlSize.navPanelPaddingV
    readonly property int paneItemHeight: Enums.controlSize.navItemHeight
    readonly property int paneCompactWidth: Enums.controlSize.navPanelCompactWidth
    readonly property int paneExpandWidth: Enums.controlSize.navPanelExpandWidth

    width: 900
    height: 900
    visible: true

    Loader {{
        objectName: "pageLoader"
        anchors.fill: parent
        source: "{page_url}"
    }}
}}
"""

# Window-level vertical navigation panels the Gallery page must demonstrate.
# 画廊页面必须展示的窗口级垂直导航面板。
# One NavigationView owns every pane display mode now: the pane expands and collapses
# in place instead of being cloned per mode.
# 现在由一个 NavigationView 覆盖所有面板显示模式: 面板在原地展开/折叠, 不再按模式克隆。
_EXPECTED_PANELS = {
    "NavigationView": 1,
    "NavigationBar": 1,
    "ToggleNavigationBar": 1,
}

# Substrings that indicate a real QML binding/loading failure rather than a
# benign runtime note. 这些子串代表真实的 QML 绑定/加载失败, 而不是无害提示。
_ERROR_MARKERS = (
    "ReferenceError",
    "TypeError",
    "is not defined",
    "Unable to assign",
    "Cannot assign",
    "Cannot read property",
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 3000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        _pump()
    return predicate()


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def _type_name(obj: QObject) -> str:
    """Strip Qt's per-registration suffix from a QML type name.

    去掉 Qt 为每次注册附加的后缀，还原 QML 类型名。
    """
    return re.sub(r"_QMLTYPE_\d+$", "", obj.metaObject().className())


def _panel_counts(root: QObject) -> dict:
    counts = {}
    for child in root.findChildren(QObject):
        name = _type_name(child)
        counts[name] = counts.get(name, 0) + 1
    return counts


def _panels_of(root: QObject, name: str) -> list:
    return [
        child
        for child in root.findChildren(QQuickItem)
        if _type_name(child) == name
    ]


def _vertical_panels_of(root: QObject, name: str) -> list:
    return [
        panel for panel in _panels_of(root, name)
        if panel.property("vertical") is True
    ]


def test_gallery_navigation_page_documents_vertical_panels():
    """The navigation page must keep showing the window-level vertical panels.

    导航页必须持续展示窗口级垂直导航面板（防止覆盖缺口回流）。
    """
    page_source = _PAGE.read_text(encoding="utf-8")
    source = _SHOWCASE.read_text(encoding="utf-8")
    for marker in (
        "NavigationView {",
        "NavigationBar {",
        "ToggleNavigationBar {",
        "Vertical navigation",
        "SegmentedControl (orientation: Qt.Vertical)",
        "Pivot (orientation: Qt.Vertical)",
    ):
        assert marker in source, marker
    assert source.count("orientation: Qt.Vertical") >= 2

    # The page itself only keeps the reference plus its own extra coverage
    assert "NavigationPanelShowcase { }" in page_source
    assert "NavigationPanelShowcase {" in page_source

    # Exactly one pane instance, driven by the mode selector 面板只保留一个实例, 由模式选择器驱动
    assert source.count("NavigationView {") == 1
    assert 'objectName: "galleryNavPane"' in source
    assert 'objectName: "galleryNavPaneModeBar"' in source
    assert "function setNavPaneMode(index)" in source
    assert "Fluent.Enums.navigation.pane_auto" in source
    # The pane must stay expandable in place 面板必须能在原地展开
    assert "galleryNavPane.toggle()" in source
    assert "galleryNavPane.togglePane()" in source
    # Each mode clone is gone for good 每种模式一个克隆的写法彻底移除
    for gone in (
        "NavigationView (compact)",
        "NavigationView (expanded)",
        "NavigationView (pane_left_minimal)",
    ):
        assert gone not in source

    # Expanding must animate and must feed the acrylic layer the way the window shell
    # does. 展开必须有动画, 并按窗口外壳的方式喂亚克力层。
    assert "Behavior on width {" in source
    assert "duration: Fluent.Enums.duration.medium" in source
    assert "navPaneFrame.isAnimating = running" in source
    assert "acrylicEnabled:" in source
    assert "acrylicImageSource:" in source
    assert "AcrylicHelper.grabAndBlur(" in source
    assert "function capturePaneAcrylic()" in source
    assert "onAboutToExpand: showcase.capturePaneAcrylic()" in source
    assert "onIsExpandedChanged: if (isExpanded) showcase.capturePaneAcrylic()" in source


def test_gallery_navigation_page_builds_vertical_panels_without_qml_errors(qapp):
    """The real Gallery page must instantiate every vertical panel with geometry.

    真实画廊页面必须无 QML 错误地实例化每个垂直面板, 并拿到非零几何。
    """
    configure_qml_environment()
    messages = []
    previous = qInstallMessageHandler(
        lambda mode, context, message: messages.append((mode, message))
    )
    engine = QQmlApplicationEngine()
    component = None
    page = None
    try:
        register_types(engine)
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(_PAGE)))
        assert _wait_until(
            lambda: component.status() != QQmlComponent.Status.Loading
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        page = component.create(engine.rootContext())
        assert page is not None, [error.toString() for error in component.errors()]
        assert _wait_until(
            lambda: all(
                len(_panels_of(page, name)) == expected
                for name, expected in _EXPECTED_PANELS.items()
            )
        ), f"panel counts: {_panel_counts(page)}"

        for name, expected in _EXPECTED_PANELS.items():
            panels = _panels_of(page, name)
            assert len(panels) == expected, f"{name}: {len(panels)} != {expected}"
            for panel in panels:
                assert panel.width() > 0, f"{name} width collapsed"
                assert panel.height() > 0, f"{name} height collapsed"
                assert panel.property("model") is not None, f"{name} lost its model"

        # Page-level vertical strips must be demonstrated too
        # 页内竖版条带同样必须被展示
        for name in ("SegmentedControl", "Pivot"):
            vertical = _vertical_panels_of(page, name)
            assert len(vertical) == 1, f"{name} vertical instances: {len(vertical)}"
            assert vertical[0].width() > 0, f"{name} vertical width collapsed"
            assert vertical[0].height() > 0, f"{name} vertical height collapsed"
    finally:
        qInstallMessageHandler(previous)
        _release(qapp, page, component, engine)

    failures = [
        message
        for mode, message in messages
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                    QtMsgType.QtFatalMsg)
        and any(marker in message for marker in _ERROR_MARKERS)
    ]
    assert failures == []


def _create_host_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        _GALLERY_HOST_SCENE.format(
            page_url=QUrl.fromLocalFile(str(_PAGE)).toString()
        ).encode("utf-8"),
        QUrl.fromLocalFile(str(_ROOT / "tests" / "qml" / "gallery-nav-host.qml")),
    )
    assert _wait_until(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    loader = window.findChild(QObject, "pageLoader")
    # Read the loaded item instead of Loader.status: the status enum has no Python
    # converter. 读取已加载项而不是 Loader.status: 该状态枚举在 Python 侧无转换器。
    assert _wait_until(lambda: loader.property("item") is not None)
    _pump(120)
    return engine, component, window, loader.property("item")


def _class_histogram(root) -> list:
    counts = {}
    for child in root.findChildren(QObject):
        name = _type_name(child)
        counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda entry: -entry[1])[:12]


def _nav_items(panel):
    """Panel rows through the sanctioned accessor.

    通过正式访问器读取面板条目: 条目由 JS 创建, QObject 树 (findChildren) 看不到它们,
    因此面板根提供 itemCount / itemAt()。
    """
    return [
        panel.itemAt(index) for index in range(panel.property("itemCount"))
    ]


def _pane(page):
    """The single merged NavigationView demo."""
    panes = [
        panel for panel in _panels_of(page, "NavigationView")
        if panel.objectName() == "galleryNavPane"
    ]
    assert len(panes) == 1, f"galleryNavPane instances: {len(panes)}"
    return panes[0]


def _click_item(window, panel, item):
    centre = item.mapToItem(
        window.contentItem(),
        QPointF(item.width() / 2, item.height() / 2),
    )
    point = QPoint(round(centre.x()), round(centre.y()))
    QTest.mouseMove(window, point)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, point,
    )


def test_gallery_vertical_panels_switch_selection_on_real_click(qapp):
    """Clicking a Gallery panel item must really move its selection.

    点击画廊面板条目必须真的改变选中项。

    回归点：NavigationPanelCore 刻意不自改 currentIndex（只发 itemClicked，交由宿主
    外壳回灌），演示里漏了这段接线时面板点不动。
    """
    engine = component = window = page = None
    try:
        engine, component, window, page = _create_host_scene(qapp)
        pane = _pane(page)
        assert pane.property("paneDisplayMode") == window.property("expandedPaneMode")
        assert pane.property("isExpanded") is True
        assert pane.property("currentIndex") == 0

        assert _wait_until(lambda: len(_nav_items(pane)) == 5), (
            f"pane items: {len(_nav_items(pane))} "
            f"size={pane.width()}x{pane.height()} "
            f"qobjects={len(pane.findChildren(QObject))} "
            f"classes={_class_histogram(pane)}"
        )
        items = _nav_items(pane)

        _click_item(window, pane, items[2])
        assert _wait_until(lambda: pane.property("currentIndex") == 2), (
            f"click did not move the selection: {pane.property('currentIndex')}"
        )

        # A second click on another row must move it again
        # 再点另一行必须继续移动
        _click_item(window, pane, items[4])
        assert _wait_until(lambda: pane.property("currentIndex") == 4), (
            f"second click did not move: {pane.property('currentIndex')}"
        )
    finally:
        if window is not None:
            window.close()
        _release(qapp, page, component, engine)


def _click_pane_toggle(window, pane):
    """Click the pane's own menu button (the expand/collapse affordance)."""
    # The button keeps the compact width and sits at the pane's leading edge, so its
    # centre stays at padding + half the compact width no matter how wide the pane is.
    # 按钮始终为紧凑宽度并贴在面板前缘, 因此无论面板多宽, 中心都是内边距 + 半个紧凑宽。
    button_width = float(pane.property("compactButtonWidth"))
    padding_h = float(window.property("panePaddingH"))
    padding_v = float(window.property("panePaddingV"))
    item_height = float(window.property("paneItemHeight"))
    centre = pane.mapToItem(
        window.contentItem(),
        QPointF(padding_h + button_width / 2, padding_v + item_height / 2),
    )
    point = QPoint(round(centre.x()), round(centre.y()))
    QTest.mouseMove(window, point)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, point,
    )


def _selector_cells(bar):
    """Cell delegate items of a SelectorBar, in visual order."""
    cells = []
    pending = [bar]
    while pending:
        node = pending.pop(0)
        for child in node.childItems():
            if _type_name(child).startswith("SelectorBarItem"):
                cells.append(child)
            else:
                pending.append(child)
    return sorted(cells, key=lambda cell: cell.x())


def _click_selector_cell(window, bar, index):
    """Click cell ``index`` of a SelectorBar through the real control.

    通过真实控件点击 SelectorBar 的第 index 个单元。
    """
    cells = _selector_cells(bar)
    assert len(cells) >= index + 1, f"mode bar cells: {len(cells)}"
    cell = cells[index]
    centre = cell.mapToItem(
        window.contentItem(),
        QPointF(cell.width() / 2, cell.height() / 2),
    )
    point = QPoint(round(centre.x()), round(centre.y()))
    QTest.mouseMove(window, point)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, point,
    )


def test_gallery_navigation_pane_collapse_is_animated(qapp):
    """Collapsing must glide the frame, not teleport it.

    折叠必须是滑行而不是瞬跳, 且亚克力层与窗口外壳用同一组输入驱动。
    """
    engine = component = window = page = None
    try:
        engine, component, window, page = _create_host_scene(qapp)
        pane = _pane(page)
        frame = page.findChild(QQuickItem, "galleryNavPaneFrame")
        assert frame is not None, "the demo has no animated frame"
        compact = float(window.property("paneCompactWidth"))
        expanded = float(window.property("paneExpandWidth"))
        assert frame.width() == pytest.approx(expanded)

        # Sample while the 200ms transition is still running 在 200ms 过渡尚未结束时采样
        _click_pane_toggle(window, pane)
        _pump(40)
        mid = frame.width()
        assert _wait_until(lambda: abs(frame.width() - compact) < 0.5), (
            f"the frame never reached the compact width: {frame.width()}"
        )
        assert compact < mid < expanded, (
            f"the frame jumped to {mid} instead of animating between {compact} and {expanded}"
        )

        # Expand again: the animation runs the other way too
        # 再次展开: 动画反向同样成立
        _click_pane_toggle(window, pane)
        _pump(40)
        mid_back = frame.width()
        assert _wait_until(lambda: abs(frame.width() - expanded) < 0.5), (
            f"the frame never returned to the design width: {frame.width()}"
        )
        assert compact < mid_back < expanded, (
            f"expanding jumped to {mid_back} instead of animating"
        )

        # Acrylic follows the same inputs as the window shell: when a capture was
        # produced, the pane must be using it while expanded.
        # 亚克力与窗口外壳用同一组输入: 抓到图后展开期间必须真的用上。
        showcase = [
            child for child in page.findChildren(QObject)
            if _type_name(child) == "NavigationPanelShowcase"
        ]
        assert len(showcase) == 1
        ready = bool(showcase[0].property("_paneAcrylicReady"))
        source = str(showcase[0].property("_paneAcrylicSource") or "")
        state_label = page.findChild(QObject, "galleryNavPaneAcrylicState")
        assert state_label is not None
        assert str(state_label.property("text")) == (
            "acrylic: on" if ready else "acrylic: off"
        )
        if ready:
            assert source != "", "acrylic reported ready without a source"
            assert pane.property("acrylicImageSource") == source
            assert pane.property("acrylicEnabled") is True
    finally:
        if window is not None:
            window.close()
        _release(qapp, page, component, engine)


def test_gallery_navigation_pane_expands_and_collapses_in_place(qapp):
    """The single pane must really expand and collapse, not be cloned per mode.

    单个面板必须真的展开与折叠, 而不是按模式克隆实例。
    """
    engine = component = window = page = None
    try:
        engine, component, window, page = _create_host_scene(qapp)
        pane = _pane(page)
        expanded_width = pane.property("implicitWidth")
        # Left mode shows the design width; the slider only drives pane_auto
        # Left 模式按设计宽度展示; 滑杆只驱动 pane_auto
        assert pane.width() == pytest.approx(expanded_width), "unexpected pane width"

        # 1. The pane's own button collapses the expanded pane to the icon rail
        # 1. 面板自己的按钮把展开态折叠成图标栏
        _click_pane_toggle(window, pane)
        assert _wait_until(lambda: pane.property("isExpanded") is False), (
            "the pane did not collapse when its menu button was clicked"
        )

        # 2. The same button expands it again 再次点击重新展开
        _click_pane_toggle(window, pane)
        assert _wait_until(lambda: pane.property("isExpanded") is True), (
            "the pane did not expand again"
        )

        # 3. The mode selector really drives the pane: compact then back to left
        # 3. 模式选择器真实驱动面板: 先紧凑再回到展开
        mode_bar = page.findChild(QObject, "galleryNavPaneModeBar")
        assert mode_bar is not None
        _click_selector_cell(window, mode_bar, 1)
        assert _wait_until(
            lambda: pane.property("paneDisplayMode")
            == window.property("compactPaneMode")
        ), "clicking Compact did not switch the pane mode"
        assert _wait_until(lambda: pane.property("isExpanded") is False)

        _click_selector_cell(window, mode_bar, 0)
        assert _wait_until(
            lambda: pane.property("paneDisplayMode")
            == window.property("expandedPaneMode")
        ), "clicking Left did not switch the pane mode"
        assert _wait_until(lambda: pane.property("isExpanded") is True)

        # 4. pane_auto follows its own width against the expand threshold
        # 4. pane_auto 按自身宽度对展开阈值做出选择
        _click_selector_cell(window, mode_bar, 3)
        assert _wait_until(
            lambda: pane.property("paneDisplayMode") == window.property("autoPaneMode")
        ), "clicking Auto did not switch the pane mode"
        slider = page.findChild(QObject, "galleryNavPaneWidth")
        assert slider is not None
        slider.setProperty("value", expanded_width)
        assert _wait_until(
            lambda: pane.property("effectivePaneDisplayMode")
            == window.property("expandedPaneMode")
        ), "pane_auto did not expand at the design width"
        slider.setProperty("value", 160)
        assert _wait_until(
            lambda: pane.property("effectivePaneDisplayMode")
            == window.property("compactPaneMode")
        ), "pane_auto did not collapse below the design width"
    finally:
        if window is not None:
            window.close()
        _release(qapp, page, component, engine)
