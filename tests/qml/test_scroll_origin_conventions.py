# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dynamic Flickable origin contracts. 动态 Flickable 原点合同。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
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
    str(ROOT / "tests" / "qml" / "scroll-origin-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick as QtQ
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root
    objectName: "window"

    function positionAtEnd() { dynamicList.positionViewAtEnd() }
    function scrollPopupToStart() { popupHelper.scrollTo(0) }

    width: 240
    height: 180
    visible: true

    QtQ.ListView {
        id: dynamicList
        objectName: "dynamicList"
        x: 20
        y: 20
        width: 180
        height: 120
        model: 90
        clip: true
        interactive: false
        delegate: Rectangle {
            required property int index
            width: ListView.view.width
            height: index % 5 === 0 ? 60 : 30
        }

        Internal.PopupSmoothScroll {
            id: popupHelper
            objectName: "popupHelper"
            flickable: dynamicList
            duration: 100
        }
    }

    ScrollBarEntry {
        id: scrollBarEntry
        objectName: "scrollBarEntry"
        x: 210
        y: 20
        height: 120
        flickable: dynamicList
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
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
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    dynamic_list = window.findChild(QQuickItem, "dynamicList")
    popup_helper = window.findChild(QQuickItem, "popupHelper")
    scroll_bar_entry = window.findChild(QQuickItem, "scrollBarEntry")
    assert dynamic_list is not None
    assert popup_helper is not None
    assert scroll_bar_entry is not None
    _pump()
    return engine, component, window, dynamic_list, popup_helper, scroll_bar_entry, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_popup_and_entry_track_dynamic_list_origin(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, dynamic_list, popup_helper, entry, warnings = scene
    try:
        thumb = next(
            item
            for item in entry.childItems()
            if item.metaObject().className().startswith("QQuickRectangle")
            and item.height() < entry.height()
        )

        assert QMetaObject.invokeMethod(window, "positionAtEnd")
        assert _wait_for(lambda: abs(dynamic_list.property("originY")) > 1)
        assert QMetaObject.invokeMethod(window, "scrollPopupToStart")
        assert _wait_for(
            lambda: dynamic_list.property("contentY")
            == pytest.approx(dynamic_list.property("originY"), abs=1),
            timeout_ms=3000,
        ), (
            dynamic_list.property("contentY"),
            dynamic_list.property("originY"),
            popup_helper.property("_targetY"),
            popup_helper.property("_smoothY"),
        )
        assert thumb.y() == pytest.approx(0, abs=1)

        start = thumb.mapToScene(
            QPointF(thumb.width() / 2, thumb.height() / 2)
        ).toPoint()
        target = start + QPoint(0, 25)
        QTest.mouseMove(window, start)
        QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(window, target, delay=20)
        QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
        assert _wait_for(
            lambda: dynamic_list.property("contentY")
            > dynamic_list.property("originY") + 1
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
