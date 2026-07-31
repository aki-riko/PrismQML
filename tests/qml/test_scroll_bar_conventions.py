# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ScrollBar component group runtime contracts. ScrollBar 组件组运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
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

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "ScrollBar"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scroll-bar-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root
    objectName: "window"

    readonly property real verticalY: verticalFlick.contentY
    readonly property real verticalTarget: verticalHelper.targetPos
    readonly property real verticalMax: verticalHelper.maxScroll
    readonly property bool verticalOvershot: verticalHelper.isOvershot
    readonly property real horizontalX: horizontalFlick.contentX
    readonly property real horizontalMax: horizontalHelper.maxScroll
    readonly property real popupY: popupFlick.contentY
    readonly property real defaultX: defaultArea.contentX
    readonly property real defaultY: defaultArea.contentY
    readonly property real defaultContentWidth: defaultArea.contentWidth
    readonly property real defaultContentHeight: defaultArea.contentHeight
    readonly property real listY: listArea.contentY
    readonly property real listContentHeight: listArea.contentHeight
    readonly property int listCount: listArea.count
    readonly property real gridY: gridArea.contentY
    readonly property real gridOriginY: gridArea.gridView.originY
    readonly property real gridContentHeight: gridArea.contentHeight
    readonly property int gridCount: gridArea.count

    function scrollVertical() { verticalHelper.scrollTo(180) }
    function scrollVerticalToEnd() { verticalHelper.scrollToEnd() }
    function growVerticalContent() { verticalFlick.contentHeight = 720 }
    function overshootVertical() { verticalHelper.scrollBy(1000) }
    function syncVertical() {
        verticalFlick.contentY = 75
        verticalHelper.syncPosition()
    }
    function scrollHorizontal() { horizontalHelper.scrollTo(260) }
    function scrollHorizontalToEnd() { horizontalHelper.scrollToEnd() }
    function growHorizontalContent() { horizontalFlick.contentWidth = 820 }
    function overshootHorizontal() { horizontalHelper.scrollBy(1000) }
    function scrollPopup() { popupHelper.scrollTo(999) }
    function setVerticalHalf() {
        verticalFlick.contentY = 240
        verticalHelper.syncPosition()
    }
    function scrollDefault() {
        defaultArea.smoothScrollTo(160)
        defaultArea.smoothScrollToX(120)
    }
    function scrollList() { listArea.scrollToIndex(10) }
    function scrollGrid() { gridArea.scrollToBottom() }

    width: 760
    height: 520
    visible: true

    Flickable {
        id: verticalFlick
        objectName: "verticalFlick"
        x: 20
        y: 20
        width: 180
        height: 120
        contentWidth: width
        contentHeight: 600
        clip: true
        interactive: false

        Rectangle {
            width: 180
            height: 600
        }
    }

    Internal.SmoothScrollHelper {
        id: verticalHelper
        objectName: "verticalHelper"
        target: verticalFlick
        duration: 100
    }

    Internal.ScrollBar {
        id: scrollBar
        objectName: "scrollBar"
        x: 210
        y: 20
        height: 120
        target: verticalFlick
        scrollHelper: verticalHelper
    }

    ScrollBarEntry {
        id: scrollBarEntry
        objectName: "scrollBarEntry"
        x: 230
        y: 20
        height: 120
        flickable: verticalFlick
    }

    Flickable {
        id: horizontalFlick
        objectName: "horizontalFlick"
        x: 20
        y: 170
        width: 180
        height: 100
        contentWidth: 700
        contentHeight: height
        clip: true
        interactive: false

        Rectangle {
            width: 700
            height: 100
        }
    }

    Internal.SmoothScrollHelper {
        id: horizontalHelper
        objectName: "horizontalHelper"
        target: horizontalFlick
        orientation: Qt.Horizontal
        duration: 100
    }

    Flickable {
        id: popupFlick
        objectName: "popupFlick"
        x: 20
        y: 300
        width: 180
        height: 100
        contentWidth: width
        contentHeight: 480
        clip: true
        interactive: false

        Rectangle {
            width: 180
            height: 480
        }

        Internal.PopupSmoothScroll {
            id: popupHelper
            objectName: "popupHelper"
            flickable: popupFlick
            duration: 100
        }
    }

    Component {
        id: listDelegate
        Rectangle {
            width: ListView.view ? ListView.view.width : 0
            height: 30
        }
    }

    Component {
        id: gridDelegate
        Rectangle {
            width: 60
            height: 40
        }
    }

    Internal.ScrollAreaDefault {
        id: defaultArea
        objectName: "defaultArea"
        x: 300
        y: 20
        width: 200
        height: 140
        padding: 10

        Rectangle {
            width: 360
            height: 420
        }
    }

    Internal.ScrollAreaList {
        id: listArea
        objectName: "listArea"
        x: 300
        y: 190
        width: 180
        height: 120
        model: 20
        delegate: listDelegate
        itemHeight: 30
    }

    Internal.ScrollAreaGrid {
        id: gridArea
        objectName: "gridArea"
        x: 520
        y: 190
        width: 180
        height: 120
        model: 20
        delegate: gridDelegate
        cellWidth: 60
        cellHeight: 40
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _wait_for_stable(predicate, stable_checks: int = 5, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    consecutive_matches = 0
    while elapsed < timeout_ms:
        QCoreApplication.processEvents(QEventLoop.AllEvents)
        consecutive_matches = consecutive_matches + 1 if predicate() else 0
        if consecutive_matches >= stable_checks:
            return True
        QTest.qSleep(10)
        elapsed += 10
    return False


def _smooth_scroll_helper(item: QQuickItem, orientation: Qt.Orientation) -> QQuickItem:
    return next(
        child
        for child in item.findChildren(QQuickItem)
        if "SmoothScrollHelper" in child.metaObject().className()
        and child.property("orientation") == orientation.value
    )


def _send_wheel(window: QQuickWindow, item: QQuickItem, delta: int) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(
        window.x() + position.x(),
        window.y() + position.y(),
    )
    event = QWheelEvent(
        position,
        global_position,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()
    items = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "verticalFlick",
            "horizontalFlick",
            "popupFlick",
            "scrollBar",
            "scrollBarEntry",
            "defaultArea",
            "listArea",
            "gridArea",
        )
    }
    assert all(items.values())
    return engine, component, window, items, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def scroll_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_smooth_helpers_clamp_animate_and_sync(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene
    assert window.property("verticalMax") == pytest.approx(480)
    assert window.property("horizontalMax") == pytest.approx(520)

    assert QMetaObject.invokeMethod(window, "scrollVertical")
    assert window.property("verticalTarget") == pytest.approx(180)
    assert _wait_for(lambda: window.property("verticalY") > 0)
    assert window.property("verticalY") < 180
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(180))

    assert QMetaObject.invokeMethod(window, "overshootVertical")
    assert window.property("verticalTarget") == pytest.approx(480)
    assert window.property("verticalOvershot")
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(480))

    assert QMetaObject.invokeMethod(window, "syncVertical")
    assert window.property("verticalTarget") == pytest.approx(75)
    assert window.property("verticalY") == pytest.approx(75)

    assert QMetaObject.invokeMethod(window, "scrollHorizontal")
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(260))
    assert QMetaObject.invokeMethod(window, "scrollHorizontalToEnd")
    assert _wait_for(
        lambda: window.property("horizontalX")
        == pytest.approx(window.property("horizontalMax"))
    )
    assert QMetaObject.invokeMethod(window, "overshootHorizontal")
    assert _wait_for(
        lambda: window.property("horizontalX") > window.property("horizontalMax")
    )
    assert _wait_for_stable(
        lambda: window.property("horizontalX")
        == pytest.approx(window.property("horizontalMax")),
        timeout_ms=1500,
    )
    assert QMetaObject.invokeMethod(window, "scrollPopup")
    assert _wait_for(lambda: window.property("popupY") == pytest.approx(380))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_area_bounce_peak_does_not_expand_after_gui_stall(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    maximum = helper.property("maxScroll")
    step = helper.property("step")

    values = []
    area.contentYChanged.connect(
        lambda: values.append(float(area.property("contentY")))
    )

    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    normal_event = _send_wheel(window, area, -120)
    assert normal_event.isAccepted()
    _pump(1000)
    normal_peak = max(values)
    assert maximum + step * 0.45 <= normal_peak <= maximum + step * 0.70
    assert area.property("contentY") == pytest.approx(maximum)

    values.clear()
    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")
    stalled_event = _send_wheel(window, area, -120)
    assert stalled_event.isAccepted()
    _pump(60)
    assert values
    before_stall = values[-1]
    resume_index = len(values)
    QTest.qSleep(120)
    _pump(1000)
    resumed_values = values[resume_index:]
    assert resumed_values
    stalled_peak = max(values)

    assert max(resumed_values) <= before_stall + 0.5
    assert stalled_peak <= normal_peak + 2
    assert area.property("contentY") == pytest.approx(maximum)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_area_boundary_bounce_does_not_restart_during_return(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    area = items["defaultArea"]
    helper = _smooth_scroll_helper(area, Qt.Orientation.Vertical)
    assert _wait_for_stable(lambda: helper.property("maxScroll") > 0)
    maximum = helper.property("maxScroll")

    values = []
    area.contentYChanged.connect(
        lambda: values.append(float(area.property("contentY")))
    )
    area.setProperty("contentY", maximum)
    assert QMetaObject.invokeMethod(helper, "syncPosition")

    first_event = _send_wheel(window, area, -120)
    assert first_event.isAccepted()
    _pump(130)
    first_peak = max(values)
    assert first_peak > maximum

    for _ in range(5):
        repeated_event = _send_wheel(window, area, -120)
        assert repeated_event.isAccepted()
        _pump(130)

    assert max(values) <= first_peak + 0.5
    assert _wait_for_stable(
        lambda: area.property("contentY") == pytest.approx(maximum),
        timeout_ms=1500,
    )

    values.clear()
    settled_event = _send_wheel(window, area, -120)
    assert settled_event.isAccepted()
    _pump(250)
    assert max(values or [maximum]) <= maximum + 0.5

    inward_event = _send_wheel(window, area, 120)
    assert inward_event.isAccepted()
    assert _wait_for(lambda: area.property("contentY") < maximum)
    _pump(1000)

    return_to_boundary_event = _send_wheel(window, area, -120)
    assert return_to_boundary_event.isAccepted()
    assert _wait_for_stable(
        lambda: area.property("contentY") == pytest.approx(maximum),
        timeout_ms=1500,
    )
    values.clear()
    unlocked_event = _send_wheel(window, area, -120)
    assert unlocked_event.isAccepted()
    assert _wait_for(lambda: max(values or [maximum]) > maximum)
    _pump(1000)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_smooth_helpers_keep_boundary_target_when_content_grows(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene

    assert QMetaObject.invokeMethod(window, "scrollVerticalToEnd")
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(480))
    assert QMetaObject.invokeMethod(window, "growVerticalContent")
    assert _wait_for(lambda: window.property("verticalMax") == pytest.approx(600))
    assert _wait_for(lambda: window.property("verticalY") == pytest.approx(600))

    assert QMetaObject.invokeMethod(window, "scrollHorizontalToEnd")
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(520))
    assert QMetaObject.invokeMethod(window, "growHorizontalContent")
    assert _wait_for(lambda: window.property("horizontalMax") == pytest.approx(640))
    assert _wait_for(lambda: window.property("horizontalX") == pytest.approx(640))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_bars_follow_position_and_real_drag(scroll_scene):
    window, items, warnings, windows_before = scroll_scene
    flick = items["verticalFlick"]
    bar = items["scrollBar"]
    entry = items["scrollBarEntry"]
    assert bar.isVisible()
    assert entry.property("active")

    assert QMetaObject.invokeMethod(window, "setVerticalHalf")
    bar_handle = next(
        item
        for item in bar.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
    )
    entry_thumb = next(
        item
        for item in entry.childItems()
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.height() < entry.height()
    )
    bar_handle_area = next(
        item
        for item in bar_handle.childItems()
        if "MouseArea" in item.metaObject().className()
    )
    assert bar_handle.height() == pytest.approx(30)
    assert entry_thumb.height() == pytest.approx(30)
    assert _wait_for(lambda: bar_handle.y() == pytest.approx(45))
    assert _wait_for(lambda: entry_thumb.y() == pytest.approx(45))

    start = bar_handle.mapToScene(
        QPointF(bar_handle.width() / 2, bar_handle.height() / 2)
    ).toPoint()
    target = start + QPoint(0, 30)
    middle = start + QPoint(0, 15)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    assert _wait_for(lambda: bar_handle_area.property("pressed"))
    QTest.mouseMove(window, middle, delay=20)
    QTest.mouseMove(window, target, delay=20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    assert _wait_for(lambda: flick.property("contentY") > 240), (
        flick.property("contentY"),
        bar_handle.y(),
    )

    values = []
    pressed = []
    released = []
    moved = []
    entry.valueChanged.connect(values.append)
    entry.sliderPressed.connect(lambda: pressed.append(True))
    entry.sliderReleased.connect(lambda: released.append(True))
    entry.sliderMoved.connect(lambda: moved.append(True))
    assert QMetaObject.invokeMethod(window, "setVerticalHalf")
    start = entry_thumb.mapToScene(
        QPointF(entry_thumb.width() / 2, entry_thumb.height() / 2)
    ).toPoint()
    target = start + QPoint(0, 25)
    middle = start + QPoint(0, 13)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, middle, delay=20)
    QTest.mouseMove(window, target, delay=20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    assert _wait_for(lambda: values and moved and released)
    assert pressed == [True]
    assert flick.property("contentY") > 240
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_area_variants_geometry_and_public_methods(scroll_scene):
    window, _items, warnings, windows_before = scroll_scene
    assert _wait_for(lambda: window.property("defaultContentWidth") == pytest.approx(380))
    assert window.property("defaultContentHeight") == pytest.approx(440)
    assert _wait_for(lambda: window.property("listCount") == 20)
    assert _wait_for(lambda: window.property("gridCount") == 20)
    assert window.property("listContentHeight") > 120
    # The vertical gutter changes this fixed scene from three to two columns.
    # 垂直避让槽会让该固定场景从三列重排为两列，滚动前必须等布局稳定。
    assert _wait_for_stable(
        lambda: window.property("gridContentHeight") == pytest.approx(400)
    )

    assert QMetaObject.invokeMethod(window, "scrollDefault")
    assert _wait_for(lambda: window.property("defaultY") == pytest.approx(160))
    assert _wait_for(lambda: window.property("defaultX") == pytest.approx(120))
    assert QMetaObject.invokeMethod(window, "scrollList")
    assert _wait_for(lambda: window.property("listY") == pytest.approx(300))
    assert QMetaObject.invokeMethod(window, "scrollGrid")
    assert _wait_for(
        lambda: window.property("gridY")
        == pytest.approx(
            window.property("gridOriginY")
            + window.property("gridContentHeight")
            - 120
        )
    ), (
        window.property("gridY"),
        window.property("gridOriginY"),
        window.property("gridContentHeight"),
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_scroll_bar_sources_follow_conventions():
    violations = []
    for source_path in sorted(SOURCE_DIR.rglob("*.qml")):
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
