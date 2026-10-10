# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Cancelable SplitView pane closing contracts. 可取消的 SplitView 面板关闭合同。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "split-view-cancel.qml")
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 700
    height: 500
    visible: false

    property bool vetoNext: false
    property int closingCount: 0
    property int closedCount: 0
    property int openedCount: 0
    property int dismissCount: 0
    property bool sawArgs: false

    function useOverlay() {
        split.displayMode = Enums.flow.split_display_overlay
    }

    function useInline() {
        split.displayMode = Enums.flow.split_display_inline
    }

    function openPane() { split.openPane() }
    function closePane() { split.closePane() }
    function togglePane() { split.togglePane() }
    function assignClosed() { split.paneOpen = false }

    SplitView {
        id: split
        objectName: "splitView"
        x: 20
        y: 20
        width: 400
        height: 300
        openPaneLength: 200
        compactPaneLength: 48
        paneMinimumSize: 60

        onPaneOpening: root.openedCount++
        onPaneClosed: root.closedCount++
        onLightDismissed: root.dismissCount++
        onPaneClosing: (args) => {
            root.closingCount++
            root.sawArgs = args !== null && args !== undefined
            if (root.vetoNext) args.cancel = true
        }

        Item { objectName: "mainContent"; anchors.fill: parent }

        paneContent: Item { objectName: "paneContent"; anchors.fill: parent }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.show()
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _split(window) -> QQuickItem:
    split = window.findChild(QQuickItem, "splitView")
    assert split is not None
    return split


def _invoke(window, name: str) -> bool:
    assert QMetaObject.invokeMethod(window, name)
    _pump()
    return True


def _click_item(window: QQuickWindow, item: QQuickItem) -> None:
    centre = item.mapToItem(
        window.contentItem(),
        item.boundingRect().center(),
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(centre.x()), round(centre.y())),
    )
    _pump(60)


def test_default_close_behavior_is_unchanged(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useInline")
        _invoke(window, "openPane")
        assert split.property("paneOpen") is True
        assert window.property("openedCount") == 1

        _invoke(window, "closePane")
        assert split.property("paneOpen") is False
        assert window.property("closedCount") == 1
        assert window.property("closingCount") == 1
        assert window.property("sawArgs") is True

        # togglePane still flips both ways 切换仍然双向生效
        _invoke(window, "togglePane")
        assert split.property("paneOpen") is True
        assert window.property("openedCount") == 2
        _invoke(window, "togglePane")
        assert split.property("paneOpen") is False
        assert window.property("closedCount") == 2
        assert window.property("closingCount") == 2
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_close_pane_can_be_vetoed(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useInline")
        _invoke(window, "openPane")

        assert window.setProperty("vetoNext", True)
        _invoke(window, "closePane")
        assert split.property("paneOpen") is True
        assert window.property("closingCount") == 1
        assert window.property("closedCount") == 0

        # Clearing the veto lets the next request through 取消否决后下一次请求生效
        assert window.setProperty("vetoNext", False)
        _invoke(window, "closePane")
        assert split.property("paneOpen") is False
        assert window.property("closingCount") == 2
        assert window.property("closedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_toggle_pane_can_be_vetoed(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useInline")
        _invoke(window, "openPane")

        assert window.setProperty("vetoNext", True)
        _invoke(window, "togglePane")
        assert split.property("paneOpen") is True
        assert window.property("closedCount") == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_light_dismiss_can_be_vetoed(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useOverlay")
        _invoke(window, "openPane")

        assert window.setProperty("vetoNext", True)
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(370, 270))
        _pump(60)
        assert split.property("paneOpen") is True
        assert window.property("dismissCount") == 0
        assert window.property("closedCount") == 0

        assert window.setProperty("vetoNext", False)
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(370, 270))
        _pump(60)
        assert split.property("paneOpen") is False
        assert window.property("dismissCount") == 1
        assert window.property("closedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_builtin_toggle_button_can_be_vetoed(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        toggle_area = split.findChild(QQuickItem, "splitViewPaneToggleArea")
        assert toggle_area is not None
        _invoke(window, "useInline")
        _invoke(window, "openPane")

        assert window.setProperty("vetoNext", True)
        _click_item(window, toggle_area)
        assert split.property("paneOpen") is True
        assert window.property("closedCount") == 0

        assert window.setProperty("vetoNext", False)
        _click_item(window, toggle_area)
        assert split.property("paneOpen") is False
        assert window.property("closedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_direct_state_assignment_still_notifies(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useInline")
        _invoke(window, "openPane")

        # A host writing paneOpen directly keeps the historical notifications
        # 宿主直接写 paneOpen 时仍保留历史通知行为
        assert window.setProperty("vetoNext", True)
        _invoke(window, "assignClosed")
        assert split.property("paneOpen") is False
        assert window.property("closingCount") == 1
        assert window.property("closedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_closed_pane_ignores_repeated_close_requests(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useInline")
        assert split.property("paneOpen") is False
        _invoke(window, "closePane")
        assert window.property("closingCount") == 0
        assert window.property("closedCount") == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_no_extra_visible_windows_are_created(qapp) -> None:
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        split = _split(window)
        _invoke(window, "useOverlay")
        _invoke(window, "openPane")
        _invoke(window, "closePane")
        assert split.property("paneOpen") is False
        assert warnings == []
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == [window]
    finally:
        _dispose_scene(engine, component, window)
