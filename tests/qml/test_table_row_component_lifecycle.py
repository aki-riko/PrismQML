# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Table row component lifecycle regressions. 表格行组件生命周期回归。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from prismqml.python.core.incubation import install_incubation_controller


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "table-row-component-lifecycle.qml")
)
EXPECTED_NORMAL_OBJECTS = 888
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 520
    height: 480
    visible: true
    color: Enums.backgroundColor

    TableWidget {
        id: table

        objectName: "table"
        x: 20
        y: 20
        width: 480
        height: 440
        showShadow: false
        columns: [
            { text: "Name", role: "name", width: 180 },
            { text: "Count", role: "count", width: 120 },
            { text: "State", role: "state", width: 150 }
        ]
        tableData: [
            { name: "Alpha", count: 1, state: "Ready" },
            { name: "Beta", count: 2, state: "Idle" },
            { name: "Gamma", count: 3, state: "Ready" },
            { name: "Delta", count: 4, state: "Idle" },
            { name: "Epsilon", count: 5, state: "Ready" },
            { name: "Zeta", count: 6, state: "Idle" },
            { name: "Eta", count: 7, state: "Ready" },
            { name: "Theta", count: 8, state: "Idle" },
            { name: "Iota", count: 9, state: "Ready" },
            { name: "Kappa", count: 10, state: "Idle" },
            { name: "Lambda", count: 11, state: "Ready" },
            { name: "Mu", count: 12, state: "Idle" }
        ]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _walk_items(root: QQuickItem):
    yield root
    for child in root.childItems():
        yield from _walk_items(child)


def _row_delegates(table: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _walk_items(table)
        if item.metaObject().indexOfProperty("editColumnIndex") >= 0
        and item.metaObject().indexOfProperty("effectiveData") >= 0
        and item.metaObject().indexOfProperty("recycling") >= 0
    ]


def _painted_rows(table: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _walk_items(table)
        if item.metaObject().indexOfProperty("extraDraw") >= 0
        and item.metaObject().indexOfProperty("rowData") >= 0
        and "PaintedRow" in item.metaObject().className()
    ]


def _component_count(owner: QObject) -> int:
    return sum(
        child.metaObject().className().startswith("QQmlComponent")
        for child in owner.findChildren(QObject)
        if child.parent() is owner
    )


def _object_count(root: QQuickItem) -> int:
    objects = {}
    for item in _walk_items(root):
        for obj in (item, *item.findChildren(QObject)):
            if shiboken6.isValid(obj):
                objects[shiboken6.getCppPointer(obj)[0]] = obj
    return len(objects)


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _grab_hash(window: QQuickWindow) -> str:
    _pump(80)
    image = window.grabWindow()
    assert not image.isNull()
    return _image_hash(image)


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    install_incubation_controller(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    table = window.findChild(QQuickItem, "table")
    assert table is not None
    assert _wait_for(lambda: len(_row_delegates(table)) >= 10)
    return engine, component, window, table, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_table_rows_preserve_rendering_while_components_are_measured(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, table, warnings = _create_scene()
    try:
        assert _wait_for(lambda: _object_count(table) == EXPECTED_NORMAL_OBJECTS)
        rows = _row_delegates(table)
        row_components = [_component_count(row) for row in rows]
        normal_objects = _object_count(table)
        normal_hash = _grab_hash(window)

        table.setProperty("paintedRowMode", True)
        assert _wait_for(lambda: len(_painted_rows(table)) == len(rows))
        painted_hash = _grab_hash(window)

        table.setProperty("paintedRowMode", False)
        assert _wait_for(lambda: _painted_rows(table) == [])
        restored_hash = _grab_hash(window)

        print(
            "TABLE_ROW_COMPONENTS",
            f"rows={len(rows)}",
            f"per_row={row_components}",
            f"objects={normal_objects}",
            f"normal_hash={normal_hash}",
            f"painted_hash={painted_hash}",
            f"restored_hash={restored_hash}",
        )

        assert len(rows) == 12
        assert row_components == [0] * 12
        assert normal_objects == EXPECTED_NORMAL_OBJECTS
        if os.name == "nt":
            assert normal_hash == (
                "866ef579e4a08cfd577606afbc3f990b"
                "eb68ef9e7f8047068b05b1a3e3db025e"
            )
            assert painted_hash == (
                "117a27de495e7ad4cc01ac2ee8d04289"
                "b2f89d8425f51b5e1fd2786820d00a69"
            )
        else:
            assert painted_hash != normal_hash
        assert restored_hash == normal_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
