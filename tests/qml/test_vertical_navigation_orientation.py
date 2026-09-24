# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vertical orientation contracts. 垂直方向契约回归。

横版行为由既有测试守住（`test_segmented_control_indicator_animation.py`、
`test_pivot_external_binding.py` 等），本文件只验证 `orientation: Qt.Vertical`
新增的主轴行为：单元自上而下堆叠、控件按堆叠高度定尺寸、指示器变成贴左边缘的竖条
并随选中项下滑到位。
"""

import pytest
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


_SCENE_DIR = Path(__file__).resolve().parent

SEGMENTED_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real expectedThickness: Enums.border.thick
    readonly property real expectedPadding: Enums.spacing.xxs * 2
    property int requestedIndex: 1

    width: 360
    height: 360
    visible: true

    SegmentedControl {
        id: segmented
        objectName: "verticalSegmented"
        orientation: Qt.Vertical
        x: 20
        y: 20
        currentIndex: root.requestedIndex
        items: [
            { key: "general", text: "General" },
            { key: "appearance", text: "Appearance" },
            { key: "advanced", text: "Advanced" }
        ]
    }
}
"""

PIVOT_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real expectedThickness: Enums.border.thick
    readonly property real expectedPadding: Enums.spacing.none
    property int requestedIndex: 1

    width: 360
    height: 360
    visible: true

    Pivot {
        id: pivot
        objectName: "verticalPivot"
        orientation: Qt.Vertical
        x: 20
        y: 20
        currentIndex: root.requestedIndex
        items: [
            { key: "general", text: "General" },
            { key: "appearance", text: "Appearance" },
            { key: "advanced", text: "Advanced" }
        ]
    }
}
"""

PIVOT_ROW_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int expectedHeight: Enums.controlSize.inputHeight

    width: 460
    height: 200
    visible: true

    Pivot {
        id: pivot
        objectName: "unSizedHorizontalPivot"
        x: 20
        y: 20
        items: [
            { key: "alpha", text: "Alpha" },
            { key: "bravo", text: "Bravo" },
            { key: "charlie", text: "Charlie" },
            { key: "delta", text: "Delta" }
        ]
    }
}
"""

TAB_BAR_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real borderThin: Enums.border.thin
    readonly property real crossPadding: Enums.spacing.xxs
    readonly property real stripInset: Enums.spacing.xs
    property int reorderCount: 0
    property int reorderedFrom: -1
    property int reorderedTo: -1
    property int addClicks: 0

    width: 460
    height: 460
    visible: true

    TabBar {
        id: bar
        objectName: "verticalTabBar"
        orientation: Qt.Vertical
        x: 20
        y: 20
        width: Enums.controlSize.tabBarVerticalWidth
        height: 400
        closable: true
        movable: true
        showAddButton: true
        currentIndex: 1
        tabs: [
            { title: "Alpha", icon: Enums.icon.folder },
            { title: "Bravo", icon: Enums.icon.folder },
            { title: "Charlie", icon: Enums.icon.folder }
        ]
        onTabsReordered: (from, to) => {
            root.reorderCount++
            root.reorderedFrom = from
            root.reorderedTo = to
        }
        onTabAddClicked: root.addClicks++
    }
}
"""


TAB_WIDGET_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real expectedStripWidth: Enums.controlSize.tabBarVerticalWidth
    property int requestedIndex: 1

    width: 520
    height: 420
    visible: true

    Component {
        id: page
        Rectangle { color: Enums.cardColor }
    }

    TabWidget {
        id: tabs
        objectName: "verticalTabWidget"
        orientation: Qt.Vertical
        x: 20
        y: 20
        width: 420
        height: 340
        currentIndex: root.requestedIndex
        tabs: [
            { title: "Alpha", content: page },
            { title: "Bravo", content: page },
            { title: "Charlie", content: page }
        ]
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _visual_descendants(root: QQuickItem):
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.childItems())


def _create_scene(qapp, source: bytes, scene_name: str):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl.fromLocalFile(str(_SCENE_DIR / scene_name)))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(80)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _parts(window: QQuickWindow, object_name: str):
    control = window.findChild(QQuickItem, object_name)
    assert control is not None
    visual = list(_visual_descendants(control))
    # Indicator geometry lives on the shared animation engine; the public base
    # item itself carries no size. 指示器几何在统一动画引擎上; 公开基类自身无尺寸。
    engines = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("indicatorX") >= 0
        and item.metaObject().indexOfProperty("leadDuration") >= 0
    ]
    delegates = sorted(
        (
            item
            for item in visual
            if item.metaObject().indexOfProperty("selected") >= 0
            and item.metaObject().indexOfProperty("key") >= 0
        ),
        key=lambda item: item.mapToItem(control, QPointF(0, 0)).y(),
    )
    assert len(engines) == 1
    assert len(delegates) == 3
    return control, engines[0], delegates


def _origins(control, delegates):
    return [item.mapToItem(control, QPointF(0, 0)) for item in delegates]


def _assert_stacked(control, window, delegates):
    origins = _origins(control, delegates)
    base = window.property("expectedPadding") / 2

    assert [origin.x() for origin in origins] == pytest.approx(
        [origins[0].x()] * 3, abs=0.01
    )
    assert origins[0].y() == pytest.approx(base, abs=0.01)
    assert origins[1].y() == pytest.approx(base + delegates[0].height(), abs=0.01)
    assert origins[2].y() == pytest.approx(
        base + delegates[0].height() + delegates[1].height(), abs=0.01
    )

    stacked = sum(item.height() for item in delegates)
    assert control.height() == pytest.approx(
        stacked + window.property("expectedPadding"), abs=0.01
    )
    # Cross axis stays content-sized, so the control never grows to the window
    # 副轴按内容定宽, 控件不会撑到窗口宽度
    assert control.width() < window.width() / 2


def _assert_indicator_tracks_selection(control, window, indicator, delegates):
    thickness = float(window.property("expectedThickness"))
    indicator_size = float(control.property("indicatorSize"))

    selected = delegates[1]
    origin = selected.mapToItem(control, QPointF(0, 0))
    assert indicator.property("indicatorWidth") == pytest.approx(
        thickness, abs=0.01
    )
    assert indicator.property("indicatorHeight") == pytest.approx(
        indicator_size, abs=0.01
    )
    assert indicator.property("indicatorX") == pytest.approx(origin.x(), abs=0.01)
    assert indicator.property("indicatorY") == pytest.approx(
        origin.y() + (selected.height() - indicator_size) / 2, abs=0.01
    )

    before_y = indicator.property("indicatorY")
    # Drive the selection through the bound root property so the control's own
    # binding path (not a direct setter call) moves the indicator.
    # 通过绑定的根属性改变选择, 让控件自身的绑定链路驱动指示器。
    window.setProperty("requestedIndex", 2)
    assert _wait_for(lambda: indicator.property("indicatorY") > before_y + 1)
    assert _wait_for(lambda: not indicator.property("running"), timeout_ms=3000)

    last = delegates[2].mapToItem(control, QPointF(0, 0))
    assert indicator.property("indicatorY") == pytest.approx(
        last.y() + (delegates[2].height() - indicator_size) / 2, abs=0.5
    )
    assert indicator.property("indicatorX") == pytest.approx(last.x(), abs=0.5)


def test_vertical_segmented_control_stacks_delegates_on_the_main_axis(qapp):
    """Vertical must stack cells top-to-bottom and size itself to the stack.

    纵向必须自上而下堆叠单元格，并按堆叠高度确定自身尺寸。
    """
    engine, component, window, warnings = _create_scene(
        qapp, SEGMENTED_SCENE, "vertical-segmented-control.qml"
    )
    try:
        control, _indicator, delegates = _parts(window, "verticalSegmented")
        _assert_stacked(control, window, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_segmented_control_moves_indicator_along_the_left_edge(qapp):
    """The indicator is a left-edge bar that slides down with the selection.

    指示器是贴左边缘的竖条，随选中项向下滑动。
    """
    engine, component, window, warnings = _create_scene(
        qapp, SEGMENTED_SCENE, "vertical-segmented-control.qml"
    )
    try:
        control, indicator, delegates = _parts(window, "verticalSegmented")
        _assert_indicator_tracks_selection(control, window, indicator, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_pivot_stacks_and_keeps_the_indicator_on_the_left_edge(qapp):
    """Pivot must mirror the same vertical contract as the segmented control.

    Pivot 的纵向契约与分段控件一致。
    """
    engine, component, window, warnings = _create_scene(
        qapp, PIVOT_SCENE, "vertical-pivot.qml"
    )
    try:
        control, indicator, delegates = _parts(window, "verticalPivot")
        _assert_stacked(control, window, delegates)
        _assert_indicator_tracks_selection(control, window, indicator, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_gallery_menu_page_documents_vertical_tab_widget():
    """The Gallery menu page must keep demonstrating vertical tabs.

    画廊菜单页必须持续展示纵向标签。
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "examples" / "pages" / "MenuPage.qml"
    ).read_text(encoding="utf-8")
    assert "TabWidget (orientation: Qt.Vertical)" in source
    assert "orientation: Qt.Vertical" in source


def test_vertical_tab_widget_puts_the_column_left_of_the_pages(qapp):
    """A vertical TabWidget must spend the leading edge on the tab column.

    纵向 TabWidget 必须把起始边让给标签列，页面占据其余区域。
    """
    engine, component, window, warnings = _create_scene(
        qapp, TAB_WIDGET_SCENE, "vertical-tab-widget.qml"
    )
    try:
        widget = window.findChild(QQuickItem, "verticalTabWidget")
        assert widget is not None
        visual = list(_visual_descendants(widget))
        bars = [
            item for item in visual
            if item.metaObject().className().startswith("TabBar")
        ]
        pages = [
            item for item in visual
            if item.metaObject().className().startswith("TabContentPages")
        ]
        assert len(bars) == 1
        assert len(pages) == 1
        bar, content = bars[0], pages[0]
        strip = window.property("expectedStripWidth")

        assert widget.property("orientation") == Qt.Orientation.Vertical.value
        assert widget.property("vertical") is True
        assert bar.property("orientation") == Qt.Orientation.Vertical.value
        assert bar.x() == pytest.approx(0, abs=0.5)
        assert bar.width() == pytest.approx(strip, abs=0.5)
        assert bar.height() == pytest.approx(widget.height(), abs=0.5)
        assert content.x() == pytest.approx(bar.width(), abs=0.5)
        assert content.width() == pytest.approx(
            widget.width() - bar.width(), abs=0.5
        )
        assert content.height() == pytest.approx(widget.height(), abs=0.5)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_horizontal_pivot_without_explicit_width_stays_on_one_row(qapp):
    """An un-sized horizontal Pivot must not wrap into stacked rows.

    未指定宽度的横向 Pivot 不得折行堆叠。

    回归点：曾把条带换成受控 Flow，positioner 的隐式尺寸因此依赖它排出的布局，
    控件隐式宽度回灌给它后横向行塌缩成 44px 并把 4 个标签折成多行。
    """
    engine, component, window, warnings = _create_scene(
        qapp, PIVOT_ROW_SCENE, "horizontal-pivot-row.qml"
    )
    try:
        pivot = window.findChild(QQuickItem, "unSizedHorizontalPivot")
        assert pivot is not None
        delegates = sorted(
            (
                item
                for item in _visual_descendants(pivot)
                if item.metaObject().indexOfProperty("selected") >= 0
                and item.metaObject().indexOfProperty("key") >= 0
            ),
            key=lambda item: item.mapToItem(pivot, QPointF(0, 0)).x(),
        )
        assert len(delegates) == 4
        origins = [item.mapToItem(pivot, QPointF(0, 0)) for item in delegates]

        origin_ys = [round(origin.y(), 1) for origin in origins]
        assert origin_ys == [origin_ys[0]] * 4, "labels wrapped onto extra rows"
        assert origins[1].x() > origins[0].x() > -0.5
        assert pivot.height() == pytest.approx(
            window.property("expectedHeight"), abs=0.5
        )
        assert pivot.width() == pytest.approx(
            sum(item.width() for item in delegates), abs=0.5
        )
        assert pivot.width() > 150, "implicit width collapsed"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def _tab_parts(window: QQuickWindow):
    bar = window.findChild(QQuickItem, "verticalTabBar")
    assert bar is not None
    visual = list(_visual_descendants(bar))
    indicators = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("_currentTabKey") >= 0
    ]
    flickables = [item for item in visual if item.inherits("QQuickFlickable")]
    delegates = sorted(
        (
            item
            for item in visual
            if item.metaObject().indexOfProperty("visualOffsetX") >= 0
            and item.metaObject().indexOfProperty("selected") >= 0
        ),
        key=lambda item: item.mapToItem(bar, QPointF(0, 0)).y(),
    )
    assert len(indicators) == 1
    assert len(flickables) == 1
    assert len(delegates) == 3
    return bar, indicators[0], flickables[0], delegates


def test_vertical_tab_bar_stacks_cells_and_keeps_the_add_button_below(qapp):
    """Vertical TabBar must stack full-width cells in a leading-edge column.

    纵向 TabBar 必须在起始边列里堆叠整宽单元，并把添加按钮放在列尾。
    """
    engine, component, window, warnings = _create_scene(
        qapp, TAB_BAR_SCENE, "vertical-tab-bar.qml"
    )
    try:
        bar, _indicator, flickable, delegates = _tab_parts(window)
        origins = [item.mapToItem(bar, QPointF(0, 0)) for item in delegates]
        cell_width = bar.width() - window.property("stripInset") * 2

        assert [round(origin.x(), 2) for origin in origins] == [
            round(origins[0].x(), 2)
        ] * 3
        assert origins[0].y() < origins[1].y() < origins[2].y()
        assert all(
            item.width() == pytest.approx(cell_width, abs=0.5)
            for item in delegates
        )
        # Vertical rows take the row height, never the tab's content width: using the
        # content width made every cell ~204px tall, so one tab filled the viewport.
        # 纵向行取行高, 绝不能取标签内容宽度: 曾用内容宽度导致每格约 204px 高,
        # 一个标签就占满视口。
        row_height = bar.property("_tabHeight")
        assert all(
            item.height() == pytest.approx(row_height, abs=0.5)
            for item in delegates
        )
        assert origins[1].y() == pytest.approx(
            origins[0].y() + row_height, abs=0.5
        )
        assert bar.property("tabRow").height() == pytest.approx(
            3 * row_height, abs=1.0
        )
        # Vertical rows carry no divider tick; one would read as a stray dash
        # 纵向行不带分隔短线; 否则会像一条多余划痕
        ticks = [
            node
            for item in delegates
            for node in _visual_descendants(item)
            if node.metaObject().indexOfProperty("lineLength") >= 0
        ]
        assert all(not tick.isVisible() for tick in ticks), (
            "vertical rows must not draw separator ticks"
        )
        # Only the column is fed a model; the idle row must stay empty
        # 只有竖列拿到模型; 闲置的横向行必须为空
        assert bar.property("tabRepeater").property("count") == 3
        assert flickable.property("contentY") == pytest.approx(0, abs=0.01)

        add_button = bar.findChild(QObject, "tabBarAddButton")
        assert add_button is not None
        assert add_button.property("visible") is True
        add_origin = add_button.mapToItem(bar, QPointF(0, 0))
        flickable_origin = flickable.mapToItem(bar, QPointF(0, 0))
        assert add_origin.y() == pytest.approx(
            flickable_origin.y() + flickable.height()
            + window.property("stripInset"),
            abs=0.5,
        )
        assert add_origin.x() + add_button.width() / 2 == pytest.approx(
            bar.width() / 2, abs=0.5
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_tab_bar_indicator_tracks_the_selected_cell(qapp):
    """The selected-cell background must slide down the column, not sideways.

    选中背景必须在列里纵向滑动，而不是横向。
    """
    engine, component, window, warnings = _create_scene(
        qapp, TAB_BAR_SCENE, "vertical-tab-bar.qml"
    )
    try:
        bar, indicator, _flickable, delegates = _tab_parts(window)
        selected = delegates[1]
        origin = selected.mapToItem(bar, QPointF(0, 0))
        thin = window.property("borderThin")

        assert indicator.isVisible()
        assert indicator.x() == pytest.approx(origin.x() + thin, abs=0.5)
        assert indicator.y() == pytest.approx(origin.y() + thin, abs=0.5)
        assert indicator.height() == pytest.approx(selected.height(), abs=0.5)
        assert indicator.width() == pytest.approx(
            selected.width() - window.property("crossPadding"), abs=0.5
        )

        close_button = next(
            (
                child
                for child in _visual_descendants(selected)
                if child.metaObject().indexOfProperty("iconSizeValue") >= 0
            ),
            None,
        )
        assert close_button is not None
        assert close_button.property("visible") is True
        close_right = close_button.mapToItem(bar, QPointF(0, 0)).x() + close_button.width()
        assert close_right <= origin.x() + selected.width() + 0.5
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_tab_bar_drag_reorders_along_the_column(qapp):
    """A real vertical drag must reorder the model and resettle the indicator.

    真实纵向拖拽必须重排模型并让指示器重新落位。
    """
    engine, component, window, warnings = _create_scene(
        qapp, TAB_BAR_SCENE, "vertical-tab-bar.qml"
    )
    try:
        bar, _indicator, _flickable, delegates = _tab_parts(window)
        start = delegates[0].mapToItem(
            window.contentItem(),
            QPointF(delegates[0].width() / 2, delegates[0].height() / 2),
        )
        target = delegates[1].mapToItem(
            window.contentItem(),
            QPointF(delegates[1].width() / 2, delegates[1].height() / 2),
        )
        start_point = QPoint(round(start.x()), round(start.y()))
        target_point = QPoint(round(target.x()), round(target.y()))
        middle_point = QPoint(
            round((start.x() + target.x()) / 2),
            round((start.y() + target.y()) / 2),
        )

        QTest.mouseMove(window, start_point)
        QTest.mousePress(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, start_point,
        )
        QTest.mouseMove(window, middle_point, 10)
        QTest.mouseMove(window, target_point, 10)
        assert bar.property("_dragging")
        QTest.mouseRelease(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, target_point,
        )

        assert _wait_for(lambda: window.property("reorderCount") == 1)
        assert window.property("reorderedFrom") == 0
        assert window.property("reorderedTo") == 1
        assert _wait_for(lambda: bar.property("currentIndex") == 1)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
