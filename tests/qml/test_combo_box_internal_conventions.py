# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Combo box internal component regressions. 下拉框内部组件回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication
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
STYLE_HELPER_SCENE = b"""
import QtQuick
import "."
import "../../../.."
Item {
    readonly property int defaultStyle: Enums.comboBox.style_default
    readonly property int primaryStyle: Enums.comboBox.style_primary
    readonly property int transparentStyle: Enums.comboBox.style_transparent
    readonly property color defaultBg: Enums.stateColor.controlBg
    readonly property color transparentBg: Enums.stateColor.controlBgTransparent
    readonly property color transparentHover: Enums.stateColor.transparentHover
    readonly property color transparentPressed: Enums.stateColor.transparentPressed
    readonly property color accentForeground: Enums.accentForeground
    readonly property color primaryText: Enums.textColor.primary
    readonly property color disabledText: Enums.textColor.disabled
    readonly property color borderStrong: Enums.stateColor.borderStrong
    property color backgroundColor: helper.getBackgroundColor()
    property color textColor: helper.getTextColor()
    property color borderColor: helper.getBorderColor()
    QtObject {
        id: fakeControl
        objectName: "control"
        property bool enabled: true
        property bool popupVisible: false
        property bool pressed: false
        property bool hovered: false
        property color accentColor: "#336699"
        property int style: 0
        property string currentText: "Selected"
    }
    ComboBoxStyleHelper { id: helper; control: fakeControl }
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


def _set_control(control, **properties) -> None:
    for name, value in properties.items():
        assert control.setProperty(name, value)
    _pump()


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


def test_combo_box_style_helper_background_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene(
        STYLE_HELPER_SCENE, "combo-box-style-helper-runtime.qml"
    )
    try:
        control = root.findChild(QObject, "control")
        accent = QColor("#336699")
        assert root.property("backgroundColor") == root.property("defaultBg")
        _set_control(control, style=root.property("primaryStyle"))
        assert root.property("backgroundColor") == accent
        _set_control(control, hovered=True)
        assert root.property("backgroundColor") == accent.lighter(108)
        _set_control(control, hovered=False, pressed=True)
        assert root.property("backgroundColor") == accent.darker(115)
        _set_control(control, pressed=False, popupVisible=True)
        assert root.property("backgroundColor") == accent.darker(110)
        _set_control(control, popupVisible=False, style=root.property("transparentStyle"))
        assert root.property("backgroundColor") == root.property("transparentBg")
        _set_control(control, hovered=True)
        assert root.property("backgroundColor") == root.property("transparentHover")
        _set_control(control, hovered=False, pressed=True)
        assert root.property("backgroundColor") == root.property("transparentPressed")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _destroy_scene(engine, component, root)


def test_combo_box_style_helper_text_and_border_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene(
        STYLE_HELPER_SCENE, "combo-box-style-helper-text-runtime.qml"
    )
    try:
        control = root.findChild(QObject, "control")
        assert root.property("textColor") == root.property("primaryText")
        assert root.property("borderColor") == root.property("borderStrong")
        _set_control(control, currentText="")
        assert root.property("textColor") == root.property("disabledText")
        _set_control(
            control, currentText="Selected", style=root.property("primaryStyle")
        )
        assert root.property("textColor") == root.property("accentForeground")
        _set_control(control, enabled=False)
        assert root.property("textColor") == root.property("disabledText")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _destroy_scene(engine, component, root)
