# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Floating label line edit regressions. 浮动标签输入框回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
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
    / "LineEdit"
    / "LineEditLabel.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "line-edit-label-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property real topY: Enums.spacing.s
    readonly property real restingScale: Enums.input.labelRestingScale
    readonly property real floatingScale:
        Enums.typography.caption / Enums.typography.body
    readonly property int labelInputHeight: Enums.controlSize.inputHeightLabel
    readonly property int textInputHeight: Enums.controlSize.inputLabelTextHeight
    readonly property string globalFont: Enums.fontFamily

    width: 320
    height: 120

    LineEdit {
        objectName: "control"
        width: 250
        inputType: Enums.input.type_label
        label: "Account"
        placeholderText: "Enter account"
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


def _descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _find_unique(root, predicate):
    matches = [child for child in _descendants(root) if predicate(child)]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _label_module(control):
    return _find_unique(
        control,
        lambda child: child.metaObject().indexOfProperty("hasContent") >= 0
        and child.metaObject().indexOfProperty("paddingLeft") >= 0
        and child.metaObject().indexOfProperty("textInput") >= 0,
    )


def _floating_label(module):
    return _find_unique(
        module,
        lambda child: child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("text") >= 0
        and child.property("text") == "Account",
    )


def _text_input(module):
    return _find_unique(
        module,
        lambda child: child.metaObject().indexOfProperty("selectByMouse") >= 0
        and child.metaObject().indexOfProperty("verticalAlignment") >= 0
        and child.metaObject().indexOfProperty("text") >= 0,
    )


@pytest.fixture
def label_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        yield root
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_line_edit_label_initial_geometry(label_scene):
    control = label_scene.findChild(QObject, "control")
    module = _label_module(control)
    floating = _floating_label(module)
    text_input = _text_input(module)
    assert control.property("implicitHeight") == label_scene.property("labelInputHeight")
    assert module.property("label") == "Account"
    assert module.property("placeholderText") == "Enter account"
    assert not module.property("hasContent")
    assert floating.property("scale") == label_scene.property("restingScale")
    expected_y = (module.property("height") - floating.property("height")) / 2
    assert floating.property("y") == pytest.approx(expected_y)
    assert text_input.property("height") == label_scene.property("textInputHeight")
    assert text_input.property("font").family() == label_scene.property("globalFont")


def test_line_edit_label_content_lifecycle(label_scene):
    control = label_scene.findChild(QObject, "control")
    module = _label_module(control)
    floating = _floating_label(module)
    emitted = []
    module.textModified.connect(emitted.append)
    module.setProperty("text", "alice")
    _pump(200)
    assert emitted[-1] == "alice"
    assert module.property("hasContent")
    assert floating.property("y") == label_scene.property("topY")
    assert floating.property("scale") == pytest.approx(
        label_scene.property("floatingScale")
    )
    assert QMetaObject.invokeMethod(module, "clear")
    _pump(200)
    assert module.property("text") == ""
    assert not module.property("hasContent")


def test_line_edit_label_enabled_binding(label_scene):
    control = label_scene.findChild(QObject, "control")
    module = _label_module(control)
    text_input = _text_input(module)
    assert text_input.property("enabled")
    control.setProperty("enabled", False)
    _pump()
    assert not text_input.property("enabled")


def test_line_edit_label_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_line_edit_label_uses_enum_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "Enums.input.labelRestingScale" in source
    assert "Enums.controlSize.inputLabelTextHeight" in source
