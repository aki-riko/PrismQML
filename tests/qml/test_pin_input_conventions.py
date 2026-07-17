# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PIN input convention regressions. PIN 输入框规范回归。"""

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
    / "PinInput.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "pin-input-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int cellSize: Enums.controlSize.pinBoxCellSize
    readonly property int cellSpacing: Enums.spacing.m
    readonly property int defaultLength: Enums.input.pinDefaultLength
    readonly property real invisibleOpacity: Enums.opacityLevel.invisible

    width: 520
    height: 100

    PinInput { objectName: "defaultPin" }
    PinInput { objectName: "customPin"; x: 320; length: 4 }
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
    if isinstance(root, QQuickItem):
        pending.extend(root.childItems())
    seen = set()
    while pending:
        child = pending.pop()
        if child in seen:
            continue
        seen.add(child)
        result.append(child)
        pending.extend(child.children())
        if isinstance(child, QQuickItem):
            pending.extend(child.childItems())
    return result


def _find_unique(root, predicate):
    matches = [child for child in _descendants(root) if predicate(child)]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _hidden_input(pin):
    return _find_unique(
        pin,
        lambda child: child.metaObject().indexOfProperty("maximumLength") >= 0
        and child.metaObject().indexOfProperty("inputMethodHints") >= 0
        and child.metaObject().indexOfProperty("text") >= 0,
    )


def _cells(pin):
    return [
        child for child in _descendants(pin)
        if child.property("hasValue") is not None
        and child.property("isCurrentCell") is not None
        and child.property("hovered") is not None
    ]


def _cell_label(cell):
    return _find_unique(
        cell,
        lambda child: child.metaObject().indexOfProperty("type") >= 0
        and child.metaObject().indexOfProperty("text") >= 0,
    )


def _cell_texts(pin):
    return [_cell_label(cell).property("text") for cell in _cells(pin)]


def _assert_password_display(pin):
    assert _cell_texts(pin).count("●") == 2
    pin.setProperty("password", False)
    _pump()
    assert sorted(label for label in _cell_texts(pin) if label) == ["1", "2"]


def _new_visible_windows(windows_before):
    return [
        window for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def test_pin_input_runtime_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        default_pin = root.findChild(QObject, "defaultPin")
        pin = root.findChild(QObject, "customPin")
        assert default_pin.property("length") == root.property("defaultLength")
        expected_width = 4 * root.property("cellSize") + 3 * root.property("cellSpacing")
        assert pin.property("implicitWidth") == expected_width
        assert pin.property("implicitHeight") == root.property("cellSize")
        hidden = _hidden_input(pin)
        assert hidden.property("maximumLength") == 4
        assert hidden.property("opacity") == root.property("invisibleOpacity")
        assert len(_cells(pin)) == 4
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_pin_input_value_lifecycle(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        pin = root.findChild(QObject, "customPin")
        hidden = _hidden_input(pin)
        modified = []
        completed = []
        pin.valueModified.connect(modified.append)
        pin.completed.connect(completed.append)
        hidden.setProperty("text", "12")
        _pump()
        assert pin.property("value") == "12"
        assert modified[-1] == "12"
        assert completed == []
        _assert_password_display(pin)
        hidden.setProperty("text", "1234")
        _pump()
        assert completed == ["1234"]
        assert QMetaObject.invokeMethod(pin, "clear")
        assert pin.property("value") == ""
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_pin_input_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_pin_input_uses_enum_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "Enums.input.pinDefaultLength" in source
    assert "Enums.input.pinEchoModeNormal" in source
    assert "Enums.input.pinMaskCharacter" in source
    assert "Enums.opacityLevel.invisible" in source
    assert "Enums.opacityLevel.visible" in source
