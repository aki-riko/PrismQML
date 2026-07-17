# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Combo box internal component regressions. 下拉框内部组件回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
INTERNAL_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "_internal"
)
SEARCH_SOURCE_PATH = INTERNAL_DIR / "PopupSearchBox.qml"
POPUP_CONTENT_SOURCE_PATH = INTERNAL_DIR / "ComboBoxPopupContent.qml"
SEARCH_SCENE = b"""
import QtQuick
import "."
Item {
    width: 200
    height: 80
    PopupSearchBox { objectName: "search"; width: parent.width }
}
"""
POPUP_CONTENT_SCENE = b"""
import QtQuick
import "."
Item {
    width: 180
    height: 90
    QtObject {
        id: fakeControl
        objectName: "control"
        property var model: ["Alpha", "Beta"]
        property int maxVisibleItems: 2
        property Component popupDelegate: null
    }
    ComboBoxPopupContent {
        objectName: "content"
        anchors.fill: parent
        control: fakeControl
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene(source: bytes, name: str):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl.fromLocalFile(str(INTERNAL_DIR / name)))
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


def _destroy_scene(engine, component, root) -> None:
    root.deleteLater()
    del component
    engine.deleteLater()
    _pump(1)


def test_popup_search_box_runtime_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene(
        SEARCH_SCENE, "popup-search-box-runtime.qml"
    )
    try:
        search = root.findChild(QObject, "search")
        assert search is not None
        enabled_height = search.property("height")
        emitted = []
        search.searchTextChanged.connect(emitted.append)
        search.setProperty("text", "alpha")
        _pump()
        assert emitted[-1] == "alpha"
        assert QMetaObject.invokeMethod(search, "clear")
        assert search.property("text") == ""
        search.setProperty("searchEnabled", False)
        assert search.property("height") == 0
        assert not search.property("visible")
        search.setProperty("searchEnabled", True)
        assert search.property("height") == enabled_height > 0
        assert search.property("visible")
        assert QMetaObject.invokeMethod(search, "focusInput")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _destroy_scene(engine, component, root)


def test_popup_search_box_source_conventions():
    source = SEARCH_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SEARCH_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_combo_box_popup_content_runtime_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene(
        POPUP_CONTENT_SCENE, "combo-box-popup-content-runtime.qml"
    )
    try:
        control = root.findChild(QObject, "control")
        content = root.findChild(QObject, "content")
        assert control is not None and content is not None
        assert content.property("width") == 180
        assert content.property("height") == 90
        assert content.property("_maxItems") == 2
        assert not content.property("needsScroll")
        control.setProperty("model", ["Alpha", "Beta", "Gamma"])
        _pump()
        assert content.property("needsScroll")
        lists = [
            child for child in _descendants(content)
            if child.metaObject().indexOfProperty("parentControl") >= 0
        ]
        assert len(lists) == 1
        assert lists[0].property("parentControl") == control
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _destroy_scene(engine, component, root)


def test_combo_box_popup_content_source_conventions():
    source = POPUP_CONTENT_SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(POPUP_CONTENT_SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []
