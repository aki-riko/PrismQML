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
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)
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
FEEDBACK_TIMER_PATH = (
    SOURCE_PATH.parent / "_internal" / "SpinBoxFeedbackTimer.qml"
)
AUTO_REPEAT_TIMER_PATH = (
    SOURCE_PATH.parent / "_internal" / "SpinBoxAutoRepeatTimer.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
INPUT_ENUM_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Input.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "spin-box-core-conventions.qml")
)
ICON_SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "spin-box-unit-icons.qml")
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


ICON_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property string walletIcon: Enums.icon.wallet
    readonly property string rewardIcon: Enums.icon.reward
    readonly property int unitIconSize: Enums.iconSize.s
    readonly property int unitIconSpacing: Enums.spacing.xs
    readonly property real valueTextWidth: valueMetrics.width

    width: 420
    height: 260
    visible: true

    TextMetrics {
        id: valueMetrics
        font.family: Enums.fontFamily
        font.pixelSize: withIcons.fontSize
        text: withIcons.displayValue
    }

    SpinBox {
        id: withIcons
        objectName: "withIcons"
        x: 40
        y: 30
        width: 220
        height: 40
        minimum: 0
        maximum: 100
        value: 42
        prefixIcon: Enums.icon.wallet
        suffixIcon: Enums.icon.reward
    }

    SpinBox {
        id: withoutIcons
        objectName: "withoutIcons"
        x: 40
        y: 100
        width: 220
        height: 40
        minimum: 0
        maximum: 100
        value: 42
    }

    SpinBox {
        id: untintedIcon
        objectName: "untintedIcon"
        x: 40
        y: 170
        width: 220
        height: 40
        minimum: 0
        maximum: 100
        value: 42
        suffixIcon: Enums.icon.reward
        iconThemeAware: false
    }

    SpinBox {
        id: typingBox
        objectName: "typingBox"
        x: 270
        y: 30
        width: Enums.controlSize.spinBoxWidth
        height: 40
        minimum: 0
        maximum: 999999999
        value: 0
        suffixIcon: Enums.icon.reward
    }

    SpinBox {
        id: typingPlain
        objectName: "typingPlain"
        x: 270
        y: 100
        width: Enums.controlSize.spinBoxWidth
        height: 40
        minimum: 0
        maximum: 999999999
        value: 0
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
    normal.selectAll()
    assert _text_input(normal).property("selectedText") == "$5.0 kg"
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
    feedback_timer_source = FEEDBACK_TIMER_PATH.read_text(encoding="utf-8")
    auto_repeat_timer_source = AUTO_REPEAT_TIMER_PATH.read_text(encoding="utf-8")
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
        "Enums.controlSize.spinBoxWidth",
    ):
        assert token in source
    assert source.count("SpinBoxInternal.SpinBoxFeedbackTimer {") == 2
    assert feedback_timer_source.count("interval: Enums.duration.fast") == 1
    assert "required property var spinControl" in feedback_timer_source
    assert "required property bool increase" in feedback_timer_source
    assert "SpinBoxInternal.SpinBoxAutoRepeatTimer {" in source
    assert "required property var spinControl" in auto_repeat_timer_source
    assert "property bool _inRepeatPhase: false" in auto_repeat_timer_source
    assert "spinControl._repeatIsUp" in auto_repeat_timer_source
    assert "readonly property int spinBoxRepeatDelay: 500" in metrics
    assert "readonly property int spinBoxRepeatInterval: 60" in metrics
    assert "readonly property int spinBoxRepeatMinInterval: 20" in metrics
    assert "readonly property real spinBoxRepeatAcceleration: 0.85" in input_enum


def test_spin_box_feedback_timer_lifecycle_contract(qapp):
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        for timer_name, is_increase in (
            ("spinBoxIncreaseFeedbackTimer", True),
            ("spinBoxDecreaseFeedbackTimer", False),
        ):
            timer = normal.findChild(QObject, timer_name)
            assert timer is not None
            assert timer.parent() is normal
            assert timer.property("spinControl") is normal
            assert timer.property("increase") is is_increase
            assert timer.property("interval") == window.property("feedbackDuration")
            assert timer.property("repeat") is False
            timer.restart()
            assert timer.property("running") is True
            assert _wait_for(lambda: timer.property("running") is False)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_spin_box_auto_repeat_timer_lifecycle_contract(qapp):
    engine, component, window, controls, warnings = _create_scene()
    try:
        normal = controls["normal"]
        timer = normal.findChild(QObject, "spinBoxAutoRepeatTimer")
        assert timer is not None
        assert timer.parent() is normal
        assert timer.property("spinControl") is normal
        assert timer.property("_inRepeatPhase") is False
        assert timer.property("interval") == normal.property("autoRepeatDelay")
        assert timer.property("repeat") is False
        timer.start()
        assert timer.property("running") is True
        assert _wait_for(lambda: timer.property("_inRepeatPhase") is True)
        assert timer.property("repeat") is True
        assert timer.property("interval") == normal.property("autoRepeatInterval")
        timer.stop()
        timer.setProperty("_inRepeatPhase", False)
        assert timer.property("running") is False
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


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


def _create_icon_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(ICON_SCENE_SOURCE, ICON_SCENE_URL)
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
        for name in (
            "withIcons",
            "withoutIcons",
            "untintedIcon",
            "typingBox",
            "typingPlain",
        )
    }
    assert all(controls.values())
    return engine, component, window, controls, warnings


def _unit_icons(spin_box):
    return (
        spin_box.findChild(QQuickItem, "spinBoxPrefixIcon"),
        spin_box.findChild(QQuickItem, "spinBoxSuffixIcon"),
    )


def _icon_images(icon):
    return [
        child
        for child in _descendants(icon)
        if child.metaObject().className() == "QQuickImage"
    ]


def _icon_image(icon):
    matches = _icon_images(icon)
    assert len(matches) == 1
    return matches[0]


def _evaluate(instance, source):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(instance), instance, source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def _assert_unit_icons_beside_value(window, spin_box):
    prefix, suffix = _unit_icons(spin_box)
    assert prefix is not None and suffix is not None
    assert prefix.isVisible() and suffix.isVisible()
    assert prefix.property("icon") == window.property("walletIcon")
    assert suffix.property("icon") == window.property("rewardIcon")
    assert prefix.width() == window.property("unitIconSize")
    assert suffix.width() == window.property("unitIconSize")
    editor = _text_input(spin_box)
    value_width = window.property("valueTextWidth")
    spacing = window.property("unitIconSpacing")
    inset = window.property("unitIconSize") + spacing
    left_padding = editor.property("leftPadding")
    right_padding = editor.property("rightPadding")
    text_width = editor.width() - left_padding - right_padding
    value_left = editor.x() + left_padding + (text_width - value_width) / 2
    value_right = value_left + value_width
    assert abs(prefix.x() + prefix.width() - (value_left - spacing)) <= 1
    assert abs(suffix.x() - (value_right + spacing)) <= 1
    # 图标单位只占内边距：输入框保持满宽，图标始终留在输入框内
    assert left_padding == inset
    assert right_padding == inset
    assert prefix.x() >= editor.x()
    assert suffix.x() + suffix.width() <= editor.x() + editor.width()


def _assert_unit_icons_hidden_without_source(spin_box):
    prefix, suffix = _unit_icons(spin_box)
    assert prefix is not None and suffix is not None
    assert not prefix.isVisible() and not suffix.isVisible()
    assert prefix.property("icon") == "" and suffix.property("icon") == ""
    assert _icon_images(prefix) == [] and _icon_images(suffix) == []


def test_spin_box_unit_icons_render_beside_the_value(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_icon_scene()
    try:
        _assert_unit_icons_beside_value(window, controls["withIcons"])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_unit_icons_keep_the_text_field_full_width(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_icon_scene()
    try:
        plain = controls["withoutIcons"]
        _assert_unit_icons_hidden_without_source(plain)
        plain_editor = _text_input(plain)
        both_editor = _text_input(controls["withIcons"])
        suffix_editor = _text_input(controls["untintedIcon"])
        inset = window.property("unitIconSize") + window.property("unitIconSpacing")
        # 图标单位用内边距占位：输入框宽度/起点与无图标时完全一致，输入与光标滚动行为不受影响
        for editor in (both_editor, suffix_editor):
            assert editor.x() == plain_editor.x()
            assert editor.width() == plain_editor.width()
        assert plain_editor.property("leftPadding") == 0
        assert plain_editor.property("rightPadding") == 0
        assert suffix_editor.property("leftPadding") == 0
        assert suffix_editor.property("rightPadding") == inset
        assert both_editor.property("leftPadding") == inset
        assert both_editor.property("rightPadding") == inset
        assert plain.property("displayValue") == controls["withIcons"].property(
            "displayValue"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def _type_digits(window, spin_box, digits):
    editor = _text_input(spin_box)
    _click(window, editor)
    assert _wait_for(lambda: editor.property("activeFocus"))
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    # QTest.keyClicks 只吃 QWidget，QQuickWindow 必须逐键发送
    for digit in digits:
        QTest.keyClick(window, getattr(Qt.Key, "Key_" + digit))
    _pump()
    return editor


def _assert_caret_visible(window, name, controls):
    spin_box = controls[name]
    editor = _type_digits(window, spin_box, "123456789")
    cursor = editor.property("cursorRectangle")
    # 光标（含其 1px 竖线在右侧边界时的位置）必须留在可见输入区内，说明视图跟着光标滚动了
    assert 0 <= cursor.x() <= editor.width(), (name, cursor.x(), editor.width())


def test_spin_box_unit_icon_keeps_caret_visible_while_typing(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_icon_scene()
    try:
        # 长数值输入时光标必须跟着走：带图标单位与无图标的行为必须一致
        _assert_caret_visible(window, "typingPlain", controls)
        _assert_caret_visible(window, "typingBox", controls)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_unit_icon_theme_awareness_controls_tinting(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_icon_scene()
    try:
        tinted = _icon_image(_unit_icons(controls["withIcons"])[1])
        untinted = _icon_image(_unit_icons(controls["untintedIcon"])[1])
        assert _wait_for(
            lambda: _evaluate(tinted, "status === Image.Ready")
            and _evaluate(untinted, "status === Image.Ready")
        )
        assert _evaluate(tinted, "layer.enabled") is True
        assert _evaluate(untinted, "layer.enabled") is False
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_unit_icon_follows_typing(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, controls, warnings = _create_icon_scene()
    try:
        spin_box = controls["typingBox"]
        icon = _unit_icons(spin_box)[1]
        # 输入过程中图标必须随数字增长实时后移（displayValue 只在提交后更新，不能拿来定位）
        before = icon.x()
        _type_digits(window, spin_box, "12345")
        assert icon.x() > before, (before, icon.x())
        assert icon.x() + icon.width() <= spin_box.width()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_spin_box_unit_icon_source_conventions_and_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    unit_path = SOURCE_PATH.parent / "_internal" / "SpinBoxUnitIcons.qml"
    assert unit_path.exists()
    unit_source = unit_path.read_text(encoding="utf-8")
    assert "SpinBoxInternal.SpinBoxUnitIcons {" in source
    for token in (
        'property string prefixIcon: ""',
        'property string suffixIcon: ""',
        "property int iconSize: Enums.iconSize.s",
        "property bool iconThemeAware: true",
    ):
        assert token in source
    assert "required property var spinControl" in unit_source
    assert "required property var textInputItem" in unit_source
    assert 'leftPadding: control.prefixIcon !== "" ? control._unitIconInset : 0' in source
    assert 'rightPadding: control.suffixIcon !== "" ? control._unitIconInset : 0' in source
    assert "clip:" not in source
    assert "TextMetrics {" in unit_source
    assert "readonly property real valueLeft" in unit_source
    assert "readonly property real textWidth" in unit_source
    assert "readonly property real iconMaxX" in unit_source
    # 定位必须用输入框实时文本，不能在提交后才更新的 displayValue
    assert "text: unitIcons.textInputItem.text" in unit_source
    assert "spinControl.displayValue" not in unit_source
    path = PurePosixPath(unit_path.relative_to(ROOT).as_posix())
    violations = scan_source_text(unit_source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML010", "QML011"}
    ] == []
