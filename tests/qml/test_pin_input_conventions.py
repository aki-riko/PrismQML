# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PIN input convention regressions. PIN 输入框规范回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import Skin, getSkin, register_types, setSkin
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
CONTENT_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "PinInputCell.qml"
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
    readonly property color accentColor: Enums.accentColor
    readonly property color accentForeground: Enums.accentForeground

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


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


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


def _cell_background(cell):
    return _cell_label(cell).parentItem()


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

        modified.clear()
        completed.clear()
        pin.setProperty("value", "98765")
        _pump()
        assert pin.property("value") == "9876"
        assert hidden.property("text") == "9876"
        assert modified == []
        assert completed == []
        assert QMetaObject.invokeMethod(pin, "selectAll")
        assert pin.property("selectedText") == "9876"
        assert QMetaObject.invokeMethod(pin, "clear")
        assert modified == [""]
        assert warnings == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_pin_input_keyboard_selection_and_editing_commands(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    clipboard = QGuiApplication.clipboard()
    previous_clipboard_text = clipboard.text()
    previous_skin = getSkin()
    engine, component, root, warnings = _create_scene()
    window = QQuickWindow()
    try:
        root.setParentItem(window.contentItem())
        window.setWidth(round(root.width()))
        window.setHeight(round(root.height()))
        window.show()
        window.requestActivate()
        assert _wait_for(window.isActive)

        pin = root.findChild(QObject, "customPin")
        hidden = _hidden_input(pin)
        first_cell = _cells(pin)[0]
        cell_point = first_cell.mapToItem(
            window.contentItem(),
            QPointF(first_cell.width() / 2, first_cell.height() / 2),
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=cell_point.toPoint(),
        )
        assert _wait_for(lambda: bool(hidden.property("activeFocus")))
        assert hidden.property("activeFocusOnTab")

        pin.setProperty("value", "1234")
        assert _wait_for(lambda: hidden.property("text") == "1234")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: pin.property("selectedText") == "1234")
        QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert _wait_for(lambda: pin.property("value") == "")

        for key in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4):
            QTest.keyClick(window, key)
        assert _wait_for(lambda: pin.property("value") == "1234")
        QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        assert _wait_for(lambda: pin.property("selectedText") == "1234")
        selected_cells = _cells(pin)
        assert all(cell.property("selected") for cell in selected_cells)
        for skin in (
            Skin.FLUENT,
            Skin.NEOBRUTALISM,
            Skin.VINTAGE_TICKET,
            Skin.NEUMORPHISM,
        ):
            setSkin(skin)
            assert _wait_for(
                lambda: all(
                    _cell_background(cell).property("color")
                    == root.property("accentColor")
                    for cell in selected_cells
                )
            )
            assert all(
                _cell_label(cell).property("color")
                == root.property("accentForeground")
                for cell in selected_cells
            )

        QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert _wait_for(lambda: pin.property("value") == "")
        assert QMetaObject.invokeMethod(pin, "undo")
        assert _wait_for(lambda: pin.property("value") == "1234")
        assert QMetaObject.invokeMethod(pin, "redo")
        assert _wait_for(lambda: pin.property("value") == "")

        for key in (Qt.Key.Key_1, Qt.Key.Key_2):
            QTest.keyClick(window, key)
        assert QMetaObject.invokeMethod(pin, "selectAll")
        assert QMetaObject.invokeMethod(pin, "copy")
        assert clipboard.text() == "12"
        assert QMetaObject.invokeMethod(pin, "cut")
        assert _wait_for(lambda: pin.property("value") == "")
        clipboard.setText("34")
        assert QMetaObject.invokeMethod(pin, "paste")
        assert _wait_for(lambda: pin.property("value") == "34")
        assert QMetaObject.invokeMethod(pin, "clear")
        assert pin.property("value") == ""
        assert warnings == []
    finally:
        setSkin(previous_skin)
        clipboard.setText(previous_clipboard_text)
        root.setParentItem(None)
        window.close()
        window.deleteLater()
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []


def test_pin_input_source_conventions():
    sources = (
        (SOURCE_PATH, SOURCE_PATH.read_text(encoding="utf-8")),
        (CONTENT_SOURCE_PATH, CONTENT_SOURCE_PATH.read_text(encoding="utf-8")),
    )
    violations = []
    for path, source in sources:
        violations.extend(
            item
            for item in scan_source_text(
                source, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if item.rule in {"QML008", "QML009"}
        )
    assert violations == []


def test_pin_input_uses_enum_tokens():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SOURCE_PATH, CONTENT_SOURCE_PATH)
    )
    for token in (
        "Enums.input.pinDefaultLength",
        "Enums.input.pinEchoModeNormal",
        "Enums.input.pinMaskCharacter",
        "Enums.opacityLevel.invisible",
        "Enums.opacityLevel.visible",
        "Enums.accentColor",
        "Enums.accentForeground",
    ):
        assert token in source
