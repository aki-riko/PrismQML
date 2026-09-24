# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SelectorBar contracts. 选择条契约回归。

用真实几何与真实点击验证：隐式尺寸、胶囊跟随、点击语义、纵向堆叠、溢出滚动
以及纵向滚轮归属。
"""

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


TEST_DIR = Path(__file__).resolve().parent
SCENE_URL = QUrl.fromLocalFile(str(TEST_DIR / "selector-bar.qml"))
SCROLL_URL = QUrl.fromLocalFile(str(TEST_DIR / "selector-bar-scroll.qml"))
BOUNDARY_URL = QUrl.fromLocalFile(str(TEST_DIR / "selector-bar-boundary.qml"))

ITEMS = """
    readonly property var sampleItems: [
        { key: "overview", text: "Overview" },
        { key: "activity", text: "Activity" },
        { key: "settings", text: "Settings", icon: "Settings" },
        { key: "about", text: "About" }
    ]
"""

# Five plain cells, matching the gallery's overflow demo 五个无图标单元, 与图库溢出示例一致
FIVE_ITEMS = """
    readonly property var sampleItems: [
        { key: "overview", text: "Overview" },
        { key: "activity", text: "Activity" },
        { key: "settings", text: "Settings" },
        { key: "about", text: "About" },
        { key: "extra", text: "Extra" }
    ]
"""

SCENE = (
    """
import QtQuick
import PrismQML

Item {
    id: root

    width: 900
    height: 460
"""
    + ITEMS
    + """
    property int clickCount: 0
    property int lastIndex: -1
    property bool lastByUser: false
    property string lastKey: ""
    // Key-based selection is driven through a property so the test exercises the
    // real QML call path instead of a meta-object invocation.
    // 按键选中通过属性驱动, 让测试走真实 QML 调用路径。
    property string keyRequest: ""
    onKeyRequestChanged: if (keyRequest !== "") bar.setCurrentItem(keyRequest)
    property int indexRequest: -1
    onIndexRequestChanged: if (indexRequest >= 0) bar.setCurrentIndex(indexRequest)

    SelectorBar {
        id: bar
        objectName: "bar"
        x: 20
        y: 20
        items: root.sampleItems
        onItemClicked: (index, byUser) => {
            root.clickCount++
            root.lastIndex = index
            root.lastByUser = byUser
        }
        onCurrentItemChanged: (key) => root.lastKey = key
    }

    SelectorBar {
        id: narrowBar
        objectName: "narrowBar"
        x: 20
        y: 140
        width: 200
        items: root.sampleItems
    }

    SelectorBar {
        id: verticalBar
        objectName: "verticalBar"
        x: 420
        y: 20
        orientation: Qt.Vertical
        items: root.sampleItems
    }
}
"""
)

SCROLL_SCENE = (
    """
import QtQuick
import PrismQML

Item {
    id: scrollRoot

    width: 600
    height: 300
"""
    + ITEMS
    + """
    Flickable {
        id: page
        objectName: "page"
        anchors.fill: parent
        contentWidth: width
        contentHeight: 1200
        boundsBehavior: Flickable.StopAtBounds

        Column {
            width: page.width

            SelectorBar {
                id: pageBar
                objectName: "pageBar"
                width: 200
                items: scrollRoot.sampleItems
            }

            SelectorBar {
                id: wideBar
                objectName: "wideBar"
                width: 600
                items: scrollRoot.sampleItems
            }

            Rectangle {
                width: parent.width
                height: 1200
                color: Enums.cardColor
            }
        }
    }
}
"""
)


# Two whole 136px cells wide: every selection but the last can start on a cell
# boundary. 宽度正好两个 136px 整格: 除最后一项外都能以单元格边界为前缘。
BOUNDARY_SCENE = (
    """
import QtQuick
import PrismQML

Item {
    id: boundaryRoot

    width: 700
    height: 200
"""
    + FIVE_ITEMS
    + """
    SelectorBar {
        id: boundaryBar
        objectName: "boundaryBar"
        x: 20
        y: 20
        width: 272
        items: boundaryRoot.sampleItems
    }
}
"""
)


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        _pump(10)
    return predicate()


def _create_scene(qapp, source: str, url: QUrl):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), url)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = QQuickWindow()
    window.resize(1000, 600)
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    root.setParentItem(window.contentItem())
    root.setSize(window.size())
    window.show()
    _pump(200)
    return engine, component, window, root, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _item(root: QQuickItem, name: str) -> QQuickItem:
    item = root.findChild(QQuickItem, name)
    assert item is not None, f"{name} not found"
    return item


def _cells(bar: QQuickItem) -> list[QQuickItem]:
    """Every SelectorBarItem cell inside the control's visual tree."""
    found: list[QQuickItem] = []
    pending = [bar]
    while pending:
        node = pending.pop(0)
        for child in node.childItems():
            if child.metaObject().className().startswith("SelectorBarItem"):
                found.append(child)
            else:
                pending.append(child)
    return found


def _pill(bar: QQuickItem) -> QQuickItem:
    item = bar.property("activePill")
    assert item is not None
    return item


def _click(window: QQuickWindow, cell: QQuickItem, local_x: float, local_y: float) -> None:
    scene_pos = cell.mapToScene(QPointF(local_x, local_y))
    point = QPoint(round(scene_pos.x()), round(scene_pos.y()))
    QTest.mouseMove(window, point)
    _pump(30)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(30)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(60)


def _send_vertical_wheel(window: QQuickWindow, item: QQuickItem) -> QWheelEvent:
    scene_pos = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    event = QWheelEvent(
        scene_pos,
        QPointF(window.x() + scene_pos.x(), window.y() + scene_pos.y()),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    _pump(240)
    return event


def test_horizontal_selector_bar_lays_cells_in_one_row(qapp):
    """Implicit size follows the strip; cells stay in a single row.

    隐式尺寸跟随条带内容, 单元保持单行。
    """
    engine, component, window, root, warnings = _create_scene(qapp, SCENE, SCENE_URL)
    try:
        bar = _item(root, "bar")
        cells = _cells(bar)
        assert len(cells) == 4
        assert [round(cell.x()) for cell in cells] == [0, 136, 272, 430]
        assert [round(cell.width()) for cell in cells] == [136, 136, 158, 94]
        assert all(
            round(cell.height()) == round(bar.property("implicitHeight"))
            for cell in cells
        )
        assert bar.property("implicitWidth") == pytest.approx(
            sum(cell.width() for cell in cells)
        )
        assert bar.property("scrollable") is False

        # The pill snaps on the first sync instead of sliding in from the origin
        # 胶囊首次同步即吸附, 不会从原点滑入
        pill = _pill(bar)
        assert bar.property("_pillReady") is False
        assert pill.property("visible") is True
        assert pill.x() == pytest.approx(0)
        assert pill.width() == pytest.approx(136)
        assert pill.height() == pytest.approx(bar.height() - 2 * pill.y())
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_real_click_selects_the_cell_and_moves_the_pill(qapp):
    """A user click selects, reports byUser and re-targets the pill.

    真实点击完成选中, 上报 byUser 并把胶囊移到该单元。
    """
    engine, component, window, root, warnings = _create_scene(qapp, SCENE, SCENE_URL)
    try:
        bar = _item(root, "bar")
        cells = _cells(bar)
        _click(window, cells[2], cells[2].width() / 2, 20)

        assert _wait_for(lambda: bar.property("currentIndex") == 2)
        assert root.property("clickCount") == 1
        assert root.property("lastIndex") == 2
        assert root.property("lastByUser") is True
        assert root.property("lastKey") == "settings"

        pill = _pill(bar)
        assert _wait_for(
            lambda: abs(pill.x() - cells[2].x()) < 0.5
            and abs(pill.width() - cells[2].width()) < 0.5
        ), "the pill did not follow the clicked cell"
        assert bar.property("_pillReady") is True
        assert cells[2].property("selected") is True
        assert cells[0].property("selected") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_programmatic_selection_never_reports_a_click(qapp):
    """Programmatic selection moves the pill without a phantom itemClicked.

    编程式选中只移动胶囊, 不产生虚假点击。
    """
    engine, component, window, root, warnings = _create_scene(qapp, SCENE, SCENE_URL)
    try:
        bar = _item(root, "bar")
        bar.setProperty("currentIndex", 2)
        _pump(120)
        assert root.property("clickCount") == 0
        assert bar.property("currentIndex") == 2

        # The API ignores an out-of-range index 公开方法忽略越界索引
        root.setProperty("indexRequest", 99)
        _pump(120)
        assert bar.property("currentIndex") == 2

        # Key-based selection resolves through the real QML call path
        # 按键选中走真实 QML 调用路径
        root.setProperty("keyRequest", "about")
        assert _wait_for(lambda: bar.property("currentIndex") == 3)
        assert root.property("clickCount") == 0

        # A key that does not exist leaves the selection alone 未知键不改变选择
        root.setProperty("keyRequest", "missing")
        _pump(120)
        assert bar.property("currentIndex") == 3

        # A raw out-of-range index must degrade instead of throwing: the pill simply
        # goes away and comes back once the selection is valid again.
        # 直接写入越界索引必须优雅退化: 胶囊消失, 选择合法后恢复。
        bar.setProperty("currentIndex", 99)
        _pump(160)
        assert _pill(bar).property("visible") is False
        bar.setProperty("currentIndex", 2)
        assert _wait_for(lambda: _pill(bar).property("visible") is True)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_selector_bar_covers_the_selected_row(qapp):
    """Vertical stacks content-sized cells and the pill covers one row.

    纵向按内容定宽堆叠, 胶囊正好覆盖选中行。
    """
    engine, component, window, root, warnings = _create_scene(qapp, SCENE, SCENE_URL)
    try:
        bar = _item(root, "verticalBar")
        cells = _cells(bar)
        assert [round(cell.y()) for cell in cells] == [0, 40, 80, 120]
        assert all(round(cell.height()) == 40 for cell in cells)
        assert bar.property("implicitHeight") == pytest.approx(160)
        assert bar.property("implicitWidth") == pytest.approx(
            max(cell.width() for cell in cells)
        )

        _click(window, cells[3], 10, 20)
        assert _wait_for(lambda: bar.property("currentIndex") == 3)
        pill = _pill(bar)
        assert _wait_for(
            lambda: abs(pill.y() - cells[3].y()) < 0.5
            and abs(pill.height() - cells[3].height()) < 0.5
        ), "the pill did not cover the selected row"
        assert cells[3].property("selected") is True
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def _settled_offset(bar: QQuickItem, timeout_ms: int = 2_000) -> float:
    """Wait until the animated scroll stops, then report the resting offset."""
    previous = float(bar.property("scrollOffset"))
    deadline = time.monotonic() + timeout_ms / 1000
    stable = 0
    while time.monotonic() < deadline:
        _pump(50)
        current = float(bar.property("scrollOffset"))
        if abs(current - previous) < 0.05:
            stable += 1
            if stable >= 3:
                return current
        else:
            stable = 0
        previous = current
    return previous


def test_narrow_selector_bar_scrolls_the_selected_cell_into_view(qapp):
    """An overflowing strip scrolls the least amount that fits the selected cell.

    条带溢出时按最小滚动量把选中单元移入可视区。
    """
    engine, component, window, root, warnings = _create_scene(qapp, SCENE, SCENE_URL)
    try:
        bar = _item(root, "narrowBar")
        assert bar.property("scrollable") is True
        assert bar.property("maxScrollOffset") == pytest.approx(
            bar.property("implicitWidth") - bar.width()
        )
        cells = _cells(bar)

        for index in (1, 2, 3):
            bar.setProperty("currentIndex", index)
            offset = _settled_offset(bar)
            cell = cells[index]
            # The selected cell is fully inside the viewport 选中单元完整落在可视区内
            assert cell.x() - offset >= -0.5
            assert cell.x() + cell.width() - offset <= bar.width() + 0.5
            # The scroll is the smallest one that achieves it, or a cell boundary
            # 滚动量是为达成该条件的最小值, 或落在某个单元格边界上
            minimal = min(
                max(0.0, cell.x() + cell.width() - bar.width()),
                float(bar.property("maxScrollOffset")),
            )
            assert offset == pytest.approx(minimal, abs=0.5) or any(
                abs(offset - other.x()) < 0.5 for other in cells
            ), f"index {index} scrolled to {offset}"

        # A cell that is visible from the very start leaves the strip unscrolled
        # 从头就完整可见的单元不产生滚动
        bar.setProperty("currentIndex", 0)
        assert _wait_for(
            lambda: float(bar.property("scrollOffset")) == pytest.approx(cells[0].x())
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_selector_bar_keeps_the_leading_edge_on_a_cell_boundary(qapp):
    """With whole cells fitting, the leading edge is a cell boundary.

    可视区能容纳整格时前缘落在单元格边界上, 不会出现半截标签。
    """
    engine, component, window, root, warnings = _create_scene(
        qapp, BOUNDARY_SCENE, BOUNDARY_URL
    )
    try:
        bar = _item(root, "boundaryBar")
        cells = _cells(bar)
        assert round(bar.width()) == 272
        assert bar.property("scrollable") is True
        assert bar.property("maxScrollOffset") == pytest.approx(
            bar.property("implicitWidth") - bar.width()
        )

        for index in (0, 1, 2, 3):
            bar.setProperty("currentIndex", index)
            offset = _settled_offset(bar)
            cell = cells[index]
            assert any(abs(offset - other.x()) < 0.5 for other in cells), (
                f"offset {offset} is not a cell boundary"
            )
            assert cell.x() - offset >= -0.5
            assert cell.x() + cell.width() - offset <= bar.width() + 0.5

        # No boundary can show the last cell: only there does the strip fall back to
        # the clamped minimal scroll. 最后一项无法对齐边界, 只有此时退化为最小滚动量。
        bar.setProperty("currentIndex", 4)
        assert _wait_for(
            lambda: float(bar.property("scrollOffset"))
            == pytest.approx(bar.property("maxScrollOffset"), abs=0.5)
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def _inner_flickable(item: QQuickItem) -> QQuickItem:
    """The strip's own scroll surface."""
    pending = [item]
    while pending:
        node = pending.pop(0)
        for child in node.childItems():
            if "Flickable" in child.metaObject().className():
                return child
            pending.append(child)
    raise AssertionError("the strip has no scroll surface")


def test_vertical_wheel_over_an_overflowing_bar_pans_the_strip(qapp):
    """A bare bar passes the wheel through; an overflowing bar pans instead.

    未溢出的条带把滚轮放行给页面; 溢出的条带自己平移, 与 TabBar 的滚轮归属一致。
    """
    engine, component, window, root, warnings = _create_scene(
        qapp, SCROLL_SCENE, SCROLL_URL
    )
    try:
        scrollable_bar = _item(root, "pageBar")
        wide_bar = _item(root, "wideBar")
        page = _item(root, "page")
        assert scrollable_bar.property("scrollable") is True
        assert wide_bar.property("scrollable") is False
        assert page.property("contentY") == pytest.approx(0)

        # A bar that cannot scroll horizontally never competes for the wheel
        # 无法横向滚动的条带根本不参与滚轮竞争
        _send_vertical_wheel(window, wide_bar)
        assert _wait_for(lambda: page.property("contentY") != 0), (
            "the vertical wheel over a non-scrollable SelectorBar never reached the page"
        )

        # An overflowing bar owns the wheel and pans its own strip
        # 溢出的条带自己拥有滚轮并平移条带
        page.setProperty("contentY", 0)
        _pump(120)
        strip = _inner_flickable(scrollable_bar)
        before_x = float(strip.property("contentX"))
        _send_vertical_wheel(window, scrollable_bar)
        assert float(strip.property("contentX")) > before_x + 1, (
            "a wheel over the overflowing strip did not pan it"
        )
        assert page.property("contentY") == pytest.approx(0)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_strip_scrolling_is_animated_not_an_instant_jump(qapp):
    """Wheel and auto-reveal moves must glide, not teleport.

    滚轮与自动滚入必须是滑行, 不能瞬跳。
    """
    engine, component, window, root, warnings = _create_scene(
        qapp, BOUNDARY_SCENE, BOUNDARY_URL
    )
    try:
        bar = _item(root, "boundaryBar")
        strip = _inner_flickable(bar)
        assert bar.property("scrollable") is True

        # Auto-reveal: sample while the move is still running
        # 自动滚入: 在位移尚未结束时采样
        bar.setProperty("currentIndex", 3)
        _pump(60)
        mid = float(strip.property("contentX"))
        assert mid > 0, "the strip never started moving"
        target = _settled_offset(bar)
        assert target > mid + 1, (
            f"auto-reveal jumped straight to {target} instead of animating (sampled {mid})"
        )
        assert strip.property("contentX") == pytest.approx(target, abs=0.5)

        # Wheel: same expectation 滚轮同理
        before = float(strip.property("contentX"))
        _send_vertical_wheel(window, bar)
        _pump(60)
        wheel_mid = float(strip.property("contentX"))
        wheel_target = _settled_offset(bar)
        assert wheel_mid != wheel_target or wheel_target == before, (
            f"the wheel jumped straight to {wheel_target} (sampled {wheel_mid})"
        )
        assert abs(wheel_target - before) > 1, "the wheel did not pan the strip"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
