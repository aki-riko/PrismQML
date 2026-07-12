# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker trigger convention regressions. 颜色选择器触发器规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "_internal"
    / "ColorPickerTrigger.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-trigger-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: scene

    readonly property int dropdownFeature: Enums.button.feature_dropdown
    readonly property color initialColor: Enums.accentColor
    readonly property color updatedColor: Enums.statusLevel.warningColor
    readonly property real triggerWidth: Enums.colorPickerMetrics.triggerWidth
    readonly property real triggerHeight: Enums.controlSize.inputHeight

    width: 240
    height: 80

    ColorPicker {
        id: picker
        objectName: "picker"
        width: scene.triggerWidth
        height: scene.triggerHeight
        type: Enums.colorPicker.type_picker
        selectedColor: scene.initialColor
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


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
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _trigger(picker):
    matches = [
        child
        for child in _descendants(picker)
        if child.metaObject().indexOfProperty("selectedColor") >= 0
        and child.metaObject().indexOfProperty("isOpen") >= 0
        and child.metaObject().indexOfProperty("implicitWidth") >= 0
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in matches
    ]
    return matches[0]


def _trigger_button(trigger):
    matches = [
        child
        for child in trigger.childItems()
        if child.metaObject().indexOfProperty("feature") >= 0
        and child.metaObject().indexOfProperty("dropdownOpen") >= 0
        and child.metaObject().indexOfProperty("style") >= 0
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in trigger.childItems()
    ]
    return matches[0]


def test_color_picker_trigger_parent_bindings(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        picker = root.findChild(QObject, "picker")
        assert picker is not None
        trigger = _trigger(picker)
        button = _trigger_button(trigger)
        assert trigger.property("selectedColor") == root.property("initialColor")
        assert not trigger.property("isOpen")
        assert trigger.property("implicitWidth") == button.property("implicitWidth")
        assert trigger.property("implicitHeight") == button.property("implicitHeight")
        assert button.property("feature") == root.property("dropdownFeature")
        assert not button.property("dropdownOpen")
        picker.setProperty("selectedColor", root.property("updatedColor"))
        picker.setProperty("enabled", False)
        picker.setProperty("_isOpen", True)
        _pump()
        assert trigger.property("selectedColor") == root.property("updatedColor")
        assert trigger.property("isOpen")
        assert not trigger.property("enabled")
        assert not button.property("enabled")
        assert button.property("dropdownOpen")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_color_picker_trigger_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item
        for item in violations
        if item.rule in {"QML008", "QML009"}
    ] == []
