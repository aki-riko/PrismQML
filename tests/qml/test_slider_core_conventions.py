# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SliderCore runtime contracts. SliderCore 运行时合同。"""

import math
from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "inputs" / "Slider" / "SliderCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "slider-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    property real methodInput: 0
    property bool methodDragging: false
    property bool customFormat: false
    readonly property real snappedValue: horizontal._maybeSnap(
        methodInput,
        methodDragging
    )
    readonly property string tipText: horizontal._tipText(methodInput)

    width: 560
    height: 330
    visible: true

    SliderCore {
        id: horizontal
        objectName: "horizontal"
        x: 60
        y: 50
        width: 300
        height: 40
        from: 0
        to: 100
        value: 40
        stepSize: 10
        snapMode: 2
        decimals: 1
        suffix: "%"
        displayValueFn: customFormat ? function(v) { return "T" + v } : null
    }

    SliderCore {
        id: vertical
        objectName: "vertical"
        x: 430
        y: 40
        width: 40
        height: 240
        from: -50
        to: 50
        value: 0
        stepSize: 10
        orientation: Qt.Vertical
    }

    SliderCore {
        id: range
        objectName: "range"
        x: 60
        y: 200
        width: 300
        height: 40
        type: Enums.slider.type_range
        from: 0
        to: 100
        firstValue: 20
        secondValue: 80
        stepSize: 10
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _local_point(window: QQuickWindow, item: QQuickItem, x: float, y: float) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
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
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in ("horizontal", "vertical", "range")
    }
    assert all(controls.values())
    assert _wait_for(lambda: all(item.childItems() for item in controls.values()))
    return engine, component, window, controls, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _default_handle(control: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(control)
        if item.metaObject().indexOfProperty("_ratio") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _range_handles(control: QQuickItem) -> list[QQuickItem]:
    matches = [
        item
        for item in _visual_descendants(control)
        if item.metaObject().indexOfProperty("handleValue") >= 0
    ]
    assert len(matches) == 2
    return sorted(matches, key=lambda item: item.property("handleValue"))


def _click_at(window: QQuickWindow, control: QQuickItem, x: float, y: float) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _local_point(window, control, x, y),
    )
    _pump()


def _drag_to(window: QQuickWindow, item: QQuickItem, target: QPoint) -> None:
    start = _point_for(window, item)
    middle = QPoint((start.x() + target.x()) // 2, (start.y() + target.y()) // 2)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, middle, 20)
    QTest.mouseMove(window, target, 20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    QTest.mouseMove(window, QPoint(520, 310))
    _pump()


def _send_wheel(window: QQuickWindow, point: QPoint, delta: int) -> None:
    global_point = window.mapToGlobal(point)
    event = QWheelEvent(
        QPointF(point),
        QPointF(global_point),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QCoreApplication.sendEvent(window, event)
    _pump()


def _assert_public_methods(window, slider) -> None:
    slider.setRange(-20, 20)
    assert (slider.property("from"), slider.property("to")) == (-20, 20)
    assert _wait_for(lambda: slider.property("value") == 20)
    slider.setValue(-99)
    assert _wait_for(lambda: slider.getValue() == -20)
    assert slider.minimum() == -20
    assert slider.maximum() == 20
    assert slider.isEnabled()
    modified = []
    slider.valueModified.connect(modified.append)
    slider.smoothSetValue(99)
    assert _wait_for(lambda: slider.getValue() == 20)
    assert modified == [20]

    window.setProperty("methodInput", 16)
    slider.setProperty("snapMode", 0)
    assert window.property("snappedValue") == 16
    slider.setProperty("snapMode", 1)
    window.setProperty("methodDragging", True)
    assert window.property("snappedValue") == 16
    window.setProperty("methodDragging", False)
    assert window.property("snappedValue") == 20


def _assert_tooltip_format(window, slider) -> None:
    window.setProperty("methodInput", 12.34)
    assert window.property("tipText") == "12.3%"
    window.setProperty("customFormat", True)
    assert window.property("tipText") == "T12.34"
    window.setProperty("customFormat", False)
    slider.setProperty("decimals", 2)
    assert window.property("tipText") == "12.34%"


def _assert_default_drag(window, slider, modified, windows_before) -> None:
    slider.setProperty("snapMode", 1)
    handle = _default_handle(slider)
    target = _local_point(window, slider, slider.width() * 0.53, 20)
    QTest.mouseMove(window, _point_for(window, handle))
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=_point_for(window, handle))
    QTest.mouseMove(window, target, 20)
    assert slider.property("_dragging")
    assert slider.property("value") == pytest.approx(0.53 * 100, abs=1.0)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    assert not slider.property("_dragging")
    assert _wait_for(lambda: slider.property("value") == 50)
    assert modified[-1] == 50
    QTest.mouseMove(window, QPoint(520, 310))
    assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])


def test_slider_public_methods_snap_and_format_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_public_methods(window, controls["horizontal"])
        _assert_tooltip_format(window, controls["horizontal"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_slider_horizontal_click_wheel_and_drag_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    slider = controls["horizontal"]
    modified = []
    slider.valueModified.connect(modified.append)
    try:
        _click_at(window, slider, slider.width() * 0.75, slider.height() / 2)
        assert _wait_for(lambda: slider.property("value") == 80)
        assert modified == [80]
        _send_wheel(window, _point_for(window, slider), -120)
        assert _wait_for(lambda: slider.property("value") == 70)
        assert modified[-1] == 70
        _assert_default_drag(window, slider, modified, windows_before)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_slider_vertical_and_range_drag_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    vertical = controls["vertical"]
    range_slider = controls["range"]
    moved = []
    range_slider.sliderMoved.connect(lambda first, second: moved.append((first, second)))
    try:
        _click_at(window, vertical, vertical.width() / 2, vertical.height() * 0.25)
        assert _wait_for(lambda: vertical.property("value") == 30)

        first_handle, second_handle = _range_handles(range_slider)
        first_target = _local_point(window, range_slider, 150, 20)
        _drag_to(window, first_handle, first_target)
        first_value = range_slider.property("firstValue")
        assert first_value > 20
        assert first_value % 10 == 0
        assert moved[-1] == (first_value, 80)

        second_target = _local_point(window, range_slider, 170, 20)
        _drag_to(window, second_handle, second_target)
        second_value = range_slider.property("secondValue")
        assert second_value < 80
        assert second_value % 10 == 0
        assert moved[-1] == (first_value, second_value)
        assert _wait_for(lambda: _new_visible_windows(windows_before, window) == [])
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_slider_core_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_slider_degenerate_ranges_and_zero_step_stay_finite(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    horizontal = controls["horizontal"]
    range_slider = controls["range"]
    try:
        horizontal.setProperty("from", 5)
        horizontal.setProperty("to", 5)
        horizontal.setProperty("value", 5)
        horizontal.setProperty("stepSize", 0)
        assert math.isfinite(float(_default_handle(horizontal).property("_ratio")))
        assert _default_handle(horizontal).property("_ratio") == 0
        assert horizontal._safeTrackPosition(5, 0) == 0
        assert horizontal._safeTrackPosition(5, -1) == 0

        range_slider.setProperty("from", 5)
        range_slider.setProperty("to", 5)
        range_slider.setProperty("firstValue", 5)
        range_slider.setProperty("secondValue", 5)
        range_impl = next(
            item
            for item in _visual_descendants(range_slider)
            if item.metaObject().indexOfProperty("firstPos") >= 0
        )
        assert math.isfinite(float(range_impl.property("firstPos")))
        assert math.isfinite(float(range_impl.property("secondPos")))
        assert range_impl.property("firstPos") == 0
        assert range_impl.property("secondPos") == 0
        assert all(
            math.isfinite(float(handle.property("x")))
            and math.isfinite(float(handle.property("y")))
            for handle in _range_handles(range_slider)
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
