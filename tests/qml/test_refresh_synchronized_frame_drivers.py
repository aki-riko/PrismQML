# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Refresh-synchronized helper lifecycle regressions. 高刷逐帧 helper 生命周期回归。"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "refresh-synchronized-frame-drivers.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import "../../prismqml/PrismQML/navigation/_internal" as NavigationInternal
import "../../prismqml/PrismQML/controls/feedback/Tooltip/_internal" as TooltipInternal

Window {
    id: root

    property int navigationUpdates: 0
    property int toggleUpdates: 0
    property int tooltipUpdates: 0

    function stopDrivers() {
        navigationDriver._scrolling = false
        toggleDriver._scrolling = false
        tooltipHost.followAnchor = false
    }

    width: 160
    height: 120
    visible: true

    QtObject {
        id: navigationHost
        function _updateIndicatorPositionRealtime() {
            root.navigationUpdates += 1
        }
    }

    QtObject {
        id: indicator
        property bool running: false
    }

    QtObject {
        id: toggleHost
        function _updateIndicator(animate) {
            root.toggleUpdates += animate ? 1000 : 1
        }
    }

    QtObject {
        id: tooltipHost
        property bool followAnchor: true
        function _reposition() {
            root.tooltipUpdates += 1
        }
    }

    QtObject {
        id: nativeHost
        property bool windowVisible: true
    }

    NavigationInternal.NavigationIndicatorTrackerTimer {
        id: navigationDriver
        objectName: "navigationFrameDriver"
        host: navigationHost
        indicator: indicator
        _scrolling: true
    }

    NavigationInternal.ToggleNavigationIndicatorTrackerTimer {
        id: toggleDriver
        objectName: "toggleFrameDriver"
        host: toggleHost
        _scrolling: true
    }

    TooltipInternal.TooltipFollowAnchorTimer {
        id: tooltipDriver
        objectName: "tooltipFrameDriver"
        host: tooltipHost
        nativeHost: nativeHost
    }
}
"""


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_refresh_synchronized_helpers_run_only_while_active(qapp):
    engine = QQmlApplicationEngine()
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    try:
        _pump(150)
        active_counts = tuple(
            window.property(name)
            for name in ("navigationUpdates", "toggleUpdates", "tooltipUpdates")
        )
        assert all(count > 0 for count in active_counts)
        for object_name in (
            "navigationFrameDriver",
            "toggleFrameDriver",
            "tooltipFrameDriver",
        ):
            driver = window.findChild(QObject, object_name)
            assert driver is not None
            assert driver.metaObject().indexOfProperty("frameTime") >= 0
            assert driver.property("running") is True

        assert QMetaObject.invokeMethod(window, "stopDrivers")
        _pump(50)
        stopped_counts = tuple(
            window.property(name)
            for name in ("navigationUpdates", "toggleUpdates", "tooltipUpdates")
        )
        _pump(100)
        settled_counts = tuple(
            window.property(name)
            for name in ("navigationUpdates", "toggleUpdates", "tooltipUpdates")
        )
        assert settled_counts == stopped_counts
    finally:
        window.close()
        for obj in (window, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
