# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Scrollable editable-input cursor contracts. 可滚动编辑输入光标合同。"""

from pathlib import Path
from time import perf_counter_ns

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scrollable-text-input-cursor-contracts.qml")
)
INPUT_PAGE_URL = (ROOT / "examples" / "pages" / "InputPage.qml").as_uri()
SCROLL_BAR_DIRECTORY_URL = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "ScrollBar"
).as_uri()
I_BEAM_CURSOR = Qt.CursorShape.IBeamCursor.value
MAX_CURSOR_EVENT_NS = 8_000_000
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 760
    height: 440
    visible: true

    ScrollArea {
        anchors.fill: parent
        padding: 0

        Item {
            width: 740
            height: 620

            LineEdit {
                objectName: "normal"
                x: 24
                y: 24
                width: 220
                text: "Normal"
            }

            LineEdit {
                objectName: "password"
                x: 24
                y: 84
                width: 220
                inputType: Enums.input.type_password
                text: "Password"
            }

            LineEdit {
                objectName: "search"
                x: 24
                y: 144
                width: 220
                inputType: Enums.input.type_search
                text: "Search"
            }

            LineEdit {
                objectName: "label"
                x: 24
                y: 204
                width: 220
                inputType: Enums.input.type_label
                label: "Account"
                text: "Label"
            }

            LineEdit {
                objectName: "tag"
                x: 24
                y: 264
                width: 300
                inputType: Enums.input.type_tag
                tags: ["Tag"]
                text: "Edit"
            }

            TextEdit {
                objectName: "plain"
                x: 370
                y: 24
                width: 250
                height: 100
                multilineType: Enums.input.multiline_plain
                text: "Plain text"
            }

            SpinBox {
                objectName: "spin"
                x: 370
                y: 154
                width: 180
                value: 5
            }

            LineEdit {
                objectName: "disabled"
                x: 370
                y: 214
                width: 220
                enabled: false
                text: "Disabled"
            }

            Item {
                x: 370
                y: 284
                width: 220
                height: 40

                LineEdit {
                    objectName: "overlap"
                    anchors.fill: parent
                    text: "Overlapped"
                }

                Item { anchors.fill: parent }
                Item { anchors.fill: parent }
            }
        }
    }

}
"""
DIRECT_SCROLL_AREA_DEFAULT_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML
import "{SCROLL_BAR_DIRECTORY_URL}" as ScrollBarInternal

Window {{
    width: 420
    height: 220
    visible: true

    ScrollBarInternal.ScrollAreaDefault {{
        objectName: "directScroll"
        anchors.fill: parent
        padding: 0

        Item {{
            width: parent.width
            height: 180

            LineEdit {{
                objectName: "directNormal"
                x: 24
                y: 24
                width: 220
                text: "Normal"
            }}

            LineEdit {{
                objectName: "directDisabled"
                x: 24
                y: 94
                width: 220
                enabled: false
                text: "Disabled"
            }}
        }}
    }}
}}
""".encode("utf-8")
GALLERY_SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window

Window {{
    width: 1200
    height: 800
    visible: true

    Loader {{
        id: inputPageLoader
        objectName: "inputPageLoader"
        anchors.fill: parent
        source: "{INPUT_PAGE_URL}"
    }}
}}
""".encode("utf-8")


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    descendants = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        descendants.append(item)
        pending.extend(item.childItems())
    return descendants


def _editable_surfaces(control: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _visual_descendants(control)
        if item.isVisible()
        and item.width() > 0
        and item.height() > 0
        and item.metaObject().className().startswith(("QQuickTextInput", "QQuickTextEdit"))
    ]


def _editable_surface(control: QQuickItem) -> QQuickItem:
    matches = _editable_surfaces(control)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _embedded_control(control: QQuickItem, class_prefix: str) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(control)
        if item.isVisible() and item.metaObject().className().startswith(class_prefix)
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _move_to_item(window: QQuickWindow, item: QQuickItem) -> None:
    QTest.mouseMove(window, QPoint(window.width() - 2, window.height() - 2))
    _pump()
    scene_point = item.mapToItem(window.contentItem(), QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseMove(window, QPoint(round(scene_point.x()), round(scene_point.y())))
    _pump(80)


def _move_to_item_with_timing(window: QQuickWindow, item: QQuickItem) -> int:
    QTest.mouseMove(window, QPoint(window.width() - 2, window.height() - 2))
    _pump()
    scene_point = item.mapToItem(window.contentItem(), QPointF(item.width() / 2, item.height() / 2))
    started_at = perf_counter_ns()
    QTest.mouseMove(window, QPoint(round(scene_point.x()), round(scene_point.y())))
    elapsed_ns = perf_counter_ns() - started_at
    _pump(80)
    return elapsed_ns


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(source: bytes):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    window.requestActivate()
    assert _wait_for(window.isActive)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_scroll_area_preserves_editable_input_cursors(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(SCENE_SOURCE)
    controls = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "normal", "password", "search", "label", "tag", "plain", "spin", "disabled", "overlap"
        )
    }
    assert all(controls.values())
    try:
        for name in ("normal", "password", "search", "label", "tag", "plain", "spin", "overlap"):
            surface = _editable_surface(controls[name])
            _move_to_item(window, surface)
            assert window.cursor().shape() == Qt.CursorShape.IBeamCursor, name

        for name, class_prefix in (
            ("normal", "CloseButton"),
            ("password", "InputActionButton"),
            ("search", "InputActionButton"),
        ):
            _move_to_item(window, _embedded_control(controls[name], class_prefix))
            assert window.cursor().shape() == Qt.CursorShape.ArrowCursor, name

        _move_to_item(window, _editable_surface(controls["disabled"]))
        assert window.cursor().shape() == Qt.CursorShape.ArrowCursor
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_direct_scroll_area_default_preserves_input_cursors(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(DIRECT_SCROLL_AREA_DEFAULT_SOURCE)
    scroll = window.findChild(QQuickItem, "directScroll")
    normal = window.findChild(QQuickItem, "directNormal")
    disabled = window.findChild(QQuickItem, "directDisabled")
    assert scroll is not None and normal is not None and disabled is not None
    try:
        _move_to_item(window, _editable_surface(normal))
        assert window.cursor().shape() == Qt.CursorShape.IBeamCursor
        _move_to_item(window, _editable_surface(disabled))
        assert window.cursor().shape() == Qt.CursorShape.ArrowCursor
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def _gallery_editable_controls(page: QQuickItem) -> list[QQuickItem]:
    items = [page, *page.findChildren(QQuickItem)]
    controls = [
        item
        for item in items
        if item.metaObject().className().startswith(("LineEditCore_QMLTYPE", "TextEditCore_QMLTYPE"))
        and item.property("cursorShape") == I_BEAM_CURSOR
        and item.property("expanded") is not False
        and len(_editable_surfaces(item)) == 1
    ]
    assert len(controls) == 8
    return controls


def test_input_page_preserves_editable_input_cursors(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    assert register_gallery_resources()
    engine, component, window, warnings = _create_scene(GALLERY_SCENE_SOURCE)
    loader = window.findChild(QQuickItem, "inputPageLoader")
    assert loader is not None
    assert _wait_for(lambda: loader.property("item") is not None)
    page = loader.property("item")
    assert isinstance(page, QQuickItem)
    try:
        controls = _gallery_editable_controls(page)
        for control in controls:
            _move_to_item(window, _editable_surface(control))
            assert window.cursor().shape() == Qt.CursorShape.IBeamCursor

        for control in controls:
            elapsed_ns = _move_to_item_with_timing(window, _editable_surface(control))
            assert elapsed_ns < MAX_CURSOR_EVENT_NS
            assert window.cursor().shape() == Qt.CursorShape.IBeamCursor

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
