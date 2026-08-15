# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Combo-box entry parent-chain regressions. 下拉框统一入口父链回归。"""

from pathlib import Path, PurePosixPath

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
    / "ComboBox"
    / "ComboBoxEntry.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-entry-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int primaryStyle: Enums.comboBox.style_primary
    readonly property int editableFeature: Enums.comboBox.feature_editable

    width: 520
    height: 160

    ComboBoxEntry {
        objectName: "syncEntry"
        width: 220
        model: []
        currentIndex: 0
    }

    ComboBoxEntry {
        objectName: "asyncEntry"
        x: 260
        width: 220
        asyncLoad: true
        model: ["Gamma", "Delta"]
        currentIndex: 1
        style: Enums.comboBox.style_primary
        feature: Enums.comboBox.feature_editable
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


def _default_combos(entry):
    return [
        child
        for child in _descendants(entry)
        if child.metaObject().indexOfProperty("editable") >= 0
        and child.metaObject().indexOfProperty("useDefaultContent") >= 0
        and child.metaObject().indexOfProperty("currentText") >= 0
        and child.metaObject().indexOfProperty("currentIndex") >= 0
    ]


def _default_combo(entry):
    matches = _default_combos(entry)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


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
    sync_entry = root.findChild(QObject, "syncEntry")
    async_entry = root.findChild(QObject, "asyncEntry")
    assert sync_entry is not None
    assert async_entry is not None
    assert _wait_for(lambda: len(_default_combos(sync_entry)) == 1)
    assert _wait_for(lambda: len(_default_combos(async_entry)) == 1)
    return engine, component, root, sync_entry, async_entry, warnings


def test_combo_box_entry_late_model_and_two_way_index_sync(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, sync_entry, async_entry, warnings = _create_scene()
    try:
        sync_combo = _default_combo(sync_entry)
        sync_entry.setProperty("model", ["Alpha", "Beta"])
        sync_entry.setProperty("currentIndex", 1)
        assert _wait_for(lambda: sync_combo.property("currentIndex") == 1)
        assert _wait_for(lambda: sync_combo.property("currentText") == "Beta")
        assert _wait_for(lambda: sync_entry.property("currentText") == "Beta")

        sync_combo.setProperty("currentIndex", 0)
        assert _wait_for(lambda: sync_entry.property("currentIndex") == 0)
        assert _wait_for(lambda: sync_entry.property("currentText") == "Alpha")

        async_combo = _default_combo(async_entry)
        assert async_combo.property("currentIndex") == 1
        assert async_combo.property("currentText") == "Delta"
        assert async_entry.property("currentText") == "Delta"
        assert async_combo.property("style") == root.property("primaryStyle")
        assert async_combo.property("feature") == root.property("editableFeature")
        assert async_combo.property("editable")
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


def test_combo_box_entry_forwards_editing_commands(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    clipboard = QGuiApplication.clipboard()
    previous_clipboard_text = clipboard.text()
    engine, component, root, sync_entry, async_entry, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(async_entry, "selectAll")
        assert async_entry.property("selectedText") == "Delta"
        assert QMetaObject.invokeMethod(async_entry, "copy")
        assert clipboard.text() == "Delta"
        assert QMetaObject.invokeMethod(async_entry, "clearEditText")
        assert _wait_for(lambda: async_entry.property("currentText") == "")
        assert async_entry.property("currentIndex") == -1
        clipboard.setText("forwarded")
        assert QMetaObject.invokeMethod(async_entry, "paste")
        assert _wait_for(lambda: async_entry.property("currentText") == "forwarded")
        assert QMetaObject.invokeMethod(async_entry, "undo")
        assert _wait_for(lambda: async_entry.property("currentText") == "")
        assert QMetaObject.invokeMethod(async_entry, "redo")
        assert _wait_for(lambda: async_entry.property("currentText") == "forwarded")
        assert warnings == []
    finally:
        clipboard.setText(previous_clipboard_text)
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        _pump()
        assert _new_visible_windows(windows_before) == []


def test_combo_box_entry_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
