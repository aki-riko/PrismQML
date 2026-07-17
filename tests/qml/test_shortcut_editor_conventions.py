# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shortcut editor runtime contracts. 快捷键编辑器运行时合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, Qt, QUrl
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
    / "ShortcutEditor.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "shortcut-editor-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: scene

    readonly property int keyCount: editor.keyList.length
    readonly property string firstKey: keyCount > 0 ? editor.keyList[0] : ""
    readonly property string secondKey: keyCount > 1 ? editor.keyList[1] : ""
    readonly property string thirdKey: keyCount > 2 ? editor.keyList[2] : ""
    property int recordedCount: 0
    property string lastRecorded: ""

    function clearShortcut() {
        editor.clear()
    }

    function resetShortcut() {
        editor.reset()
    }

    width: 360
    height: 120
    visible: false

    ShortcutEditor {
        id: editor
        objectName: "editor"
        anchors.centerIn: parent
        width: 260
        shortcut: "Ctrl+Shift+A"
        defaultShortcut: "Alt+B"

        onShortcutRecorded: (value) => {
            scene.recordedCount += 1
            scene.lastRecorded = value
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    editor = root.findChild(QObject, "editor")
    assert editor is not None
    return engine, component, root, editor, warnings


def test_shortcut_editor_public_methods_and_recording_lifecycle(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, editor, warnings = _create_scene()
    try:
        assert root.property("keyCount") == 3
        assert root.property("firstKey") == "Ctrl"
        assert root.property("secondKey") == "Shift"
        assert root.property("thirdKey") == "A"
        assert editor.property("shortcut") == "Ctrl+Shift+A"
        assert not editor.property("recording")

        assert QMetaObject.invokeMethod(
            root, "clearShortcut", Qt.ConnectionType.DirectConnection
        )
        _pump()
        assert editor.property("shortcut") == ""
        assert root.property("keyCount") == 0
        assert root.property("recordedCount") == 1
        assert root.property("lastRecorded") == ""

        assert QMetaObject.invokeMethod(
            root, "resetShortcut", Qt.ConnectionType.DirectConnection
        )
        _pump()
        assert editor.property("shortcut") == "Alt+B"
        assert root.property("keyCount") == 2
        assert root.property("firstKey") == "Alt"
        assert root.property("secondKey") == "B"
        assert root.property("recordedCount") == 2
        assert root.property("lastRecorded") == "Alt+B"

        for _ in range(3):
            assert editor.setProperty("recording", True)
            _pump()
            assert editor.property("recording")
            assert editor.property("focused")
            assert editor.setProperty("recording", False)
            _pump()
            assert not editor.property("recording")

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


def test_shortcut_editor_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
