# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Progress viewport detection regressions. 进度条视口检测回归。"""

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
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
BAR_IMPL = (
    QML_ROOT / "controls" / "feedback" / "Progress" / "_internal"
    / "ProgressBarImpl.qml"
)
RING_IMPL = BAR_IMPL.with_name("ProgressRingImpl.qml")

SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    readonly property Item barImpl: insideBarLoader.item
    readonly property Item ringImpl: insideRingLoader.item
    readonly property Item offscreenBarImpl: offscreenBarLoader.item

    function scrollDown() { viewport.contentY = 700 }
    function scrollTop() { viewport.contentY = 0 }
    function hideBar() { insideBar.visible = false }
    function showBar() { insideBar.visible = true }

    width: 240
    height: 140
    visible: true

    Flickable {
        id: viewport
        objectName: "viewport"
        anchors.fill: parent
        contentWidth: width
        contentHeight: 900

        Progress {
            id: insideBar
            objectName: "insideBar"
            y: 10
            width: 180
            indeterminate: true
        }

        Progress {
            id: insideRing
            objectName: "insideRing"
            y: 40
            type: Enums.progress.type_ring
            indeterminate: true
            running: true
        }

        // Far below the viewport at startup. 启动时远在视口下方。
        Progress {
            id: offscreenBar
            objectName: "offscreenBar"
            y: 700
            width: 180
            indeterminate: true
        }
    }

    // Reach the impls through each Loader. 通过各自的 Loader 取到实现体。
    readonly property Loader insideBarLoader: insideBar.children[0]
    readonly property Loader insideRingLoader: insideRing.children[0]
    readonly property Loader offscreenBarLoader: offscreenBar.children[0]
}
""".encode("utf-8")


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


def test_progress_impls_pause_animation_outside_viewport(qapp):
    """离屏进度条必须停止动画, 包括启动时就在屏外的那一个。

    Both progress implementations gate their indeterminate animations on
    ``_isInViewport``. An implementation that reports true while parked far below
    the fold keeps a GPU animation running forever, which is the regression this
    gate blocks.
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("inline:progress-viewport.qml"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    try:
        bar = window.property("barImpl")
        ring = window.property("ringImpl")
        offscreen = window.property("offscreenBarImpl")
        assert bar is not None
        assert ring is not None
        assert offscreen is not None

        # Visible ones animate. 视口内的照常动画。
        assert _wait_for(lambda: bar.property("_isInViewport") is True)
        assert _wait_for(lambda: ring.property("_isInViewport") is True)

        # Parked far below the fold, it must be paused from the start.
        # 启动时就远在折叠线以下的那个必须一开始就是暂停的。
        assert _wait_for(lambda: offscreen.property("_isInViewport") is False)

        # Scrolling down brings it in and pushes the top ones out.
        # 向下滚动让它进入视口，同时把顶部的推出视口。
        assert QMetaObject.invokeMethod(window, "scrollDown")
        assert _wait_for(lambda: offscreen.property("_isInViewport") is True)
        assert _wait_for(lambda: bar.property("_isInViewport") is False)
        assert _wait_for(lambda: ring.property("_isInViewport") is False)

        assert QMetaObject.invokeMethod(window, "scrollTop")
        assert _wait_for(lambda: bar.property("_isInViewport") is True)

        # Hiding the host pauses it even while scrolled into view.
        # 即使处在视口内，隐藏宿主也要暂停。
        assert QMetaObject.invokeMethod(window, "hideBar")
        assert _wait_for(lambda: bar.property("_isInViewport") is False)
        assert QMetaObject.invokeMethod(window, "showBar")
        assert _wait_for(lambda: bar.property("_isInViewport") is True)

        assert warnings == []
    finally:
        window.close()
        for obj in (window, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == []
