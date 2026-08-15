# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Cycle wheel picker parent-chain regressions. 循环滚轮选择器父链回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "CycleWheelPicker.qml"
)
CONTENT_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "_internal"
    / "CycleWheelPickerButtons.qml"
)
PATH_DELEGATE_SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "_internal"
    / "CycleWheelPickerPathDelegate.qml"
)
LIST_DELEGATE_SOURCE_PATH = PATH_DELEGATE_SOURCE_PATH.with_name(
    "CycleWheelPickerListDelegate.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "cycle-wheel-picker-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedRepeatDelay: Enums.duration.wheelPickerRepeatDelay
    readonly property int expectedRepeatInterval: Enums.duration.wheelPickerRepeatInterval
    readonly property int expectedMaxFlickVelocity: Enums.controlSize.wheelPickerMaxFlickVelocity
    readonly property int expectedFlickDeceleration: Enums.controlSize.wheelPickerFlickDeceleration

    width: 420
    height: 360

    CycleWheelPicker {
        objectName: "cyclePicker"
        x: 40
        width: 140
        items: ["Alpha", "Beta", "Gamma"]
        currentIndex: 1
        cycle: true
        showScrollButtons: false
    }

    CycleWheelPicker {
        objectName: "linearPicker"
        x: 220
        width: 140
        items: ["Alpha", "Beta", "Gamma"]
        currentIndex: 1
        cycle: false
        showScrollButtons: false
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


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    cycle_picker = root.findChild(QObject, "cyclePicker")
    linear_picker = root.findChild(QObject, "linearPicker")
    assert cycle_picker is not None
    assert linear_picker is not None
    assert _wait_for(lambda: cycle_picker.property("currentValue") == "Beta")
    assert _wait_for(lambda: linear_picker.property("currentValue") == "Beta")
    return engine, component, root, cycle_picker, linear_picker, warnings


def test_cycle_wheel_picker_public_methods_wrap_and_clamp(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, cycle_picker, linear_picker, warnings = _create_scene()
    try:
        cycle_changes = []
        cycle_picker.currentItemChanged.connect(
            lambda index, value: cycle_changes.append((index, value))
        )
        cycle_picker.scrollDown()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 2)
        cycle_picker.scrollDown()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 0)
        cycle_picker.scrollUp()
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 2)
        assert cycle_changes == [
            (2, "Gamma"),
            (0, "Alpha"),
            (2, "Gamma"),
        ]
        cycle_picker.setCurrentValue("Beta")
        assert _wait_for(lambda: cycle_picker.property("currentIndex") == 1)
        assert cycle_picker.getCurrentIndex() == 1
        assert cycle_picker.currentItem() == "Beta"
        assert cycle_changes[-1] == (2, "Gamma")

        linear_picker.setCurrentIndex(0)
        linear_picker.scrollUp()
        _pump()
        assert linear_picker.property("currentIndex") == 0
        linear_picker.scrollDown()
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 1)
        linear_picker.setCurrentIndex(2)
        linear_picker.scrollDown()
        _pump()
        assert linear_picker.property("currentIndex") == 2

        linear_picker.setProperty("items", ["Only"])
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 0)
        assert _wait_for(lambda: linear_picker.property("currentValue") == "Only")

        list_views = [
            child
            for child in _descendants(linear_picker)
            if isinstance(child, QQuickItem)
            and "QQuickListView" in child.metaObject().className()
        ]
        assert len(list_views) == 1
        assert list_views[0].property("maximumFlickVelocity") == root.property(
            "expectedMaxFlickVelocity"
        )
        assert list_views[0].property("flickDeceleration") == root.property(
            "expectedFlickDeceleration"
        )

        repeat_timers = [
            child
            for child in _descendants(linear_picker)
            if child.metaObject().indexOfProperty("interval") >= 0
            and child.metaObject().indexOfProperty("repeat") >= 0
            and child.property("repeat")
            and child.property("interval") == root.property("expectedRepeatDelay")
        ]
        assert len(repeat_timers) == 1
        assert repeat_timers[0].parent() is linear_picker
        linear_picker.setProperty("_repeatStarted", True)
        _pump()
        assert all(
            timer.property("interval") == root.property("expectedRepeatInterval")
            for timer in repeat_timers
        )
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []


def test_cycle_wheel_picker_repeat_timers_preserve_both_directions(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, _cycle_picker, linear_picker, warnings = _create_scene()
    try:
        descendants = _descendants(linear_picker)
        repeat_timers = [
            child
            for child in descendants
            if child.metaObject().indexOfProperty("interval") >= 0
            and child.metaObject().indexOfProperty("repeat") >= 0
            and child.property("repeat")
            and child.property("interval") == root.property("expectedRepeatDelay")
        ]
        assert len(descendants) == 33
        assert len(repeat_timers) == 1

        repeat_timer = repeat_timers[0]
        linear_picker.setCurrentIndex(1)
        linear_picker._startRepeat(-1)
        assert repeat_timer.property("running")
        assert QMetaObject.invokeMethod(repeat_timer, "triggered")
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 0)
        assert repeat_timer.property("interval") == root.property(
            "expectedRepeatInterval"
        )
        linear_picker._stopRepeat(-1)
        assert not repeat_timer.property("running")

        linear_picker.setCurrentIndex(1)
        linear_picker._startRepeat(1)
        assert repeat_timer.property("running")
        assert QMetaObject.invokeMethod(repeat_timer, "triggered")
        assert _wait_for(lambda: linear_picker.property("currentIndex") == 2)
        linear_picker._stopRepeat(1)
        assert not repeat_timer.property("running")

        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []


def test_cycle_wheel_picker_source_conventions_and_motion_tokens():
    sources = (
        (SOURCE_PATH, SOURCE_PATH.read_text(encoding="utf-8")),
        (CONTENT_SOURCE_PATH, CONTENT_SOURCE_PATH.read_text(encoding="utf-8")),
        (
            PATH_DELEGATE_SOURCE_PATH,
            PATH_DELEGATE_SOURCE_PATH.read_text(encoding="utf-8"),
        ),
        (
            LIST_DELEGATE_SOURCE_PATH,
            LIST_DELEGATE_SOURCE_PATH.read_text(encoding="utf-8"),
        ),
    )
    violations = []
    for path, source in sources:
        violations.extend(
            violation
            for violation in scan_source_text(
                source, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []
    source = SOURCE_PATH.read_text(encoding="utf-8")
    for token in (
        "Enums.duration.wheelPickerRepeatInterval",
        "Enums.duration.wheelPickerRepeatDelay",
        "Enums.controlSize.wheelPickerMaxFlickVelocity",
        "Enums.controlSize.wheelPickerFlickDeceleration",
    ):
        assert token in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int wheelPickerRepeatInterval: 50" in metrics
    assert "readonly property int wheelPickerRepeatDelay: 500" in metrics
    assert "readonly property int wheelPickerMaxFlickVelocity: 800" in metrics
    assert "readonly property int wheelPickerFlickDeceleration: 1500" in metrics
