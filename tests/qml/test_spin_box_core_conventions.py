# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SpinBoxCore runtime contracts. SpinBoxCore 运行时合同。"""

from pathlib import Path, PurePosixPath

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
from PySide6.QtTest import QSignalSpy, QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "SpinBox"
    / "SpinBoxCore.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
INPUT_ENUM_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Input.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "spin-box-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property string subtractIcon: Enums.icon.subtract
    readonly property string addIcon: Enums.icon.add
    readonly property int inputInteractionZ: Enums.zIndex.inputInteraction
    readonly property int inputControlsZ: Enums.zIndex.inputControls
    readonly property int repeatDelay: Enums.duration.spinBoxRepeatDelay
    readonly property int repeatInterval: Enums.duration.spinBoxRepeatInterval
    readonly property int repeatMinInterval: Enums.duration.spinBoxRepeatMinInterval
    readonly property real repeatAcceleration: Enums.input.spinBoxRepeatAcceleration
    readonly property int feedbackDuration: Enums.duration.fast
    readonly property int spinBoxWidth: Enums.controlSize.spinBoxWidth
    readonly property int compactType: Enums.input.spinbox_compact

    width: 620
    height: 300
    visible: true

    Item {
        id: background
        objectName: "background"
        anchors.fill: parent
        focus: true

        MouseArea {
            anchors.fill: parent
            onClicked: background.forceActiveFocus()
        }
    }

    SpinBox {
        id: normal
        objectName: "normal"
        x: 60
        y: 50
        width: 180
        height: 40
        minimum: 0
        maximum: 10
        value: 5
        stepSize: 2
        decimals: 1
        prefix: "$"
        suffix: " kg"
    }

    SpinBox {
        id: wrapped
        objectName: "wrapped"
        x: 60
        y: 130
        width: 160
        height: 40
        minimum: 0
        maximum: 2
        value: 2
        wrap: true
    }

    SpinBox {
        id: bounded
        objectName: "bounded"
        x: 300
        y: 50
        width: 160
        height: 40
        minimum: 0
        maximum: 6
        value: 5
        autoRepeatDelay: 30
        autoRepeatInterval: 20
        autoRepeatMinInterval: 20
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


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
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
        for name in ("background", "normal", "wrapped", "bounded")
    }
    assert all(controls.values())
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


def _button_with_icon(window, spin_box, property_name):
    icon = window.property(property_name)
    matches = [
        child
        for child in _descendants(spin_box)
        if child.metaObject().indexOfProperty("preferredHeight") >= 0
        and child.metaObject().indexOfProperty("icon") >= 0
        and child.property("icon") == icon
    ]
    assert len(matches) == 1
    return matches[0]


def _text_input(spin_box):
    matches = [
        child
        for child in _descendants(spin_box)
        if child.metaObject().indexOfProperty("validator") >= 0
        and child.metaObject().indexOfProperty("selectByMouse") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _input_interaction_layer(spin_box):
    matches = [
        child
        for child in spin_box.childItems()
        if child.metaObject().indexOfProperty("propagateComposedEvents") >= 0
        and child.property("propagateComposedEvents")
        and child.property("acceptedButtons") == Qt.MouseButton.LeftButton
    ]
    assert len(matches) == 1
    return matches[0]


def _timers(spin_box):
    return [
        child
        for child in spin_box.children()
        if child.metaObject().indexOfProperty("interval") >= 0
        and child.metaObject().indexOfProperty("repeat") >= 0
    ]


def _click(window, item) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point_for(window, item),
    )
    _pump()


def _send_wheel(window, item, delta: int) -> None:
    point = _point_for(window, item)
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


def _assert_public_methods(normal, wrapped) -> None:
    updates = []
    modified = []
    normal.valueUpdated.connect(updates.append)
    normal.valueModified.connect(modified.append)
    assert normal.property("displayValue") == "$5.0 kg"
    normal.setRange(0, 6)
    normal.increase()
    assert (normal.getValue(), updates, modified) == (6, [6], [6])
    normal.increase()
    assert (updates, modified) == ([6], [6])
    normal.decrease()
    assert normal.getValue() == 4
    normal.setValue(-99)
    assert normal.getValue() == 0
    normal.decrease()
    assert (updates, modified) == ([6, 4], [6, 4])
    normal.stepUp()
    assert normal.getValue() == 2

    wrapped_updates = []
    wrapped.valueModified.connect(wrapped_updates.append)
    wrapped.increase()
    wrapped.decrease()
    assert (wrapped.getValue(), wrapped_updates) == (2, [0, 2])


def _assert_default_tokens(window, normal) -> None:
    assert normal.property("autoRepeatDelay") == window.property("repeatDelay")
    assert normal.property("autoRepeatInterval") == window.property("repeatInterval")
    assert normal.property("autoRepeatMinInterval") == window.property(
        "repeatMinInterval"
    )
    assert normal.property("_repeatCurrentInterval") == window.property(
        "repeatInterval"
    )
    assert window.property("repeatAcceleration") == 0.85
    assert normal.property("implicitWidth") == window.property("spinBoxWidth")
    timers = _timers(normal)
    assert len(timers) == 3
    intervals = [timer.property("interval") for timer in timers]
    assert intervals.count(window.property("repeatDelay")) >= 1
    assert intervals.count(window.property("feedbackDuration")) >= 2


def _assert_text_edit(window, normal) -> None:
    editor = _text_input(normal)
    _click(window, editor)
    assert _wait_for(lambda: editor.property("activeFocus"))
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(window, Qt.Key.Key_8)
    QTest.keyClick(window, Qt.Key.Key_Period)
    QTest.keyClick(window, Qt.Key.Key_5)
    QTest.keyClick(window, Qt.Key.Key_Return)
    assert _wait_for(lambda: normal.property("value") == 8.5)
    assert normal.property("displayValue") == "$8.5 kg"


def _assert_wheel_focus_gate(window, controls) -> None:
    normal = controls["normal"]
    _click(window, controls["background"])
    assert not _text_input(normal).property("activeFocus")
    _send_wheel(window, normal, 120)
    assert normal.property("value") == 5
    _click(window, _text_input(normal))
    _send_wheel(window, normal, 120)
    assert normal.property("value") == 7


def _assert_button_layer_and_repeat_stops_at_bound(window, bounded) -> None:
    values = []
    bounded.valueModified.connect(values.append)
    button = _button_with_icon(window, bounded, "addIcon")
    assert button.property("z") == window.property("inputControlsZ")
    assert _input_interaction_layer(bounded).property("z") == window.property(
        "inputInteractionZ"
    )
    point = _point_for(window, button)
    QTest.mouseMove(window, point)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point)
    _pump(130)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=point)
    assert _wait_for(lambda: bounded.property("value") == 6)
    assert values == [6]
    count_after_release = len(values)
    _pump(80)
    assert len(values) == count_after_release


def test_spin_box_public_methods_wrap_and_signal_characterization(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_default_tokens(window, controls["normal"])
        _assert_public_methods(controls["normal"], controls["wrapped"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_core_source_conventions_and_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    input_enum = INPUT_ENUM_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    for token in (
        "Enums.duration.spinBoxRepeatDelay",
        "Enums.duration.spinBoxRepeatInterval",
        "Enums.duration.spinBoxRepeatMinInterval",
        "Enums.input.spinBoxRepeatAcceleration",
        "Enums.controlSize.spinBoxWidth",
    ):
        assert token in source
    assert source.count("interval: Enums.duration.fast") == 2
    assert "readonly property int spinBoxRepeatDelay: 500" in metrics
    assert "readonly property int spinBoxRepeatInterval: 60" in metrics
    assert "readonly property int spinBoxRepeatMinInterval: 20" in metrics
    assert "readonly property real spinBoxRepeatAcceleration: 0.85" in input_enum


def test_spin_box_text_edit_and_wheel_focus_contracts(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_text_edit(window, controls["normal"])
        controls["normal"].setValue(5)
        _assert_wheel_focus_gate(window, controls)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_button_layer_and_repeat_signal_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        _assert_button_layer_and_repeat_stops_at_bound(window, controls["bounded"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_repeat_phase_timing_and_live_delay_binding(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        normal.setProperty("value", 0)
        normal.setProperty("maximum", 1000)
        normal.setProperty("stepSize", 1)
        normal.setProperty("autoRepeatDelay", 80)
        normal.setProperty("autoRepeatInterval", 60)
        normal.setProperty("autoRepeatMinInterval", 60)
        values = []
        normal.valueModified.connect(values.append)

        normal._startAutoRepeat(True)
        running = [timer for timer in _timers(normal) if timer.property("running")]
        assert len(running) == 1
        assert running[0].property("interval") == 80
        normal.setProperty("autoRepeatDelay", 100)
        assert _wait_for(lambda: running[0].property("interval") == 100)

        normal._stopAutoRepeat()
        auto_repeat_timer = running[0]
        timer_triggered = QSignalSpy(auto_repeat_timer.triggered)
        normal.setProperty("autoRepeatDelay", 80)
        normal._startAutoRepeat(True)
        assert _wait_for(lambda: timer_triggered.count() >= 1)
        assert values == []
        assert auto_repeat_timer.property("interval") == 60
        assert auto_repeat_timer.property("repeat")
        assert _wait_for(lambda: timer_triggered.count() >= 2)
        assert values == [1]
        normal._stopAutoRepeat()
        _pump(100)
        assert values == [1]

        normal.setProperty("autoRepeatDelay", 30)
        normal.setProperty("autoRepeatInterval", 20)
        normal.setProperty("autoRepeatMinInterval", 10)
        triggered_count = timer_triggered.count()
        normal._startAutoRepeat(True)
        assert _wait_for(lambda: timer_triggered.count() >= triggered_count + 3)
        assert values[-1] > 1
        normal._stopAutoRepeat()
        assert auto_repeat_timer.property("interval") == 30
        assert not auto_repeat_timer.property("repeat")

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_double_click_changes_value_exactly_twice(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        values = []
        normal.valueModified.connect(values.append)
        increase_button = _button_with_icon(window, normal, "addIcon")
        QTest.mouseDClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, increase_button),
        )
        _pump()
        assert (normal.property("value"), values) == (9, [7, 9])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_mode_switch_cancels_held_repeat(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        normal.setProperty("maximum", 1000)
        normal.setProperty("autoRepeatDelay", 30)
        normal.setProperty("autoRepeatInterval", 20)
        normal.setProperty("autoRepeatMinInterval", 20)
        increase_button = _button_with_icon(window, normal, "addIcon")
        point = _point_for(window, increase_button)

        QTest.mouseMove(window, point)
        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point)
        _pump(110)
        assert normal.property("value") > 5

        normal.setProperty("type", window.property("compactType"))
        _pump()
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=point)
        _pump()
        value_after_release = normal.property("value")
        _pump(160)

        assert normal.property("value") == value_after_release
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
