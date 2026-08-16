# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Smooth-scroll frame-driver regressions. 平滑滚动逐帧驱动回归。"""

from __future__ import annotations

import os
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
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "smooth-scroll-frame-driver.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar" as Internal

Window {
    id: root

    readonly property real position: flickable.contentY

    function startScroll() {
        helper.scrollTo(180)
    }

    width: 240
    height: 180
    visible: true

    Flickable {
        id: flickable
        width: parent.width
        height: parent.height
        contentWidth: width
        contentHeight: 640
        interactive: false
    }

    Internal.SmoothScrollHelper {
        id: helper
        objectName: "smoothScrollHelper"
        target: flickable
        duration: 120
        easing: Easing.OutCubic
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


def test_smooth_scroll_frame_driver_runs_only_during_motion(qapp):
    """Frame drivers are idle at rest and preserve the requested end position.

    逐帧驱动器仅在运动期间运行，并保持请求的最终位置。
    """
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    helper = window.findChild(QQuickItem, "smoothScrollHelper")
    vertical = window.findChild(QObject, "smoothScrollVerticalFrameDriver")
    horizontal = window.findChild(QObject, "smoothScrollHorizontalFrameDriver")
    try:
        assert helper is not None
        assert vertical is not None
        assert horizontal is not None
        assert vertical.property("running") is False
        assert horizontal.property("running") is False

        assert QMetaObject.invokeMethod(window, "startScroll")
        assert _wait_for(lambda: vertical.property("running") is True)
        assert horizontal.property("running") is False
        completed = _wait_for(
            lambda: window.property("position") == 180
            and vertical.property("running") is False
        )
        assert completed, {
            "position": window.property("position"),
            "running": vertical.property("running"),
            "from": vertical.property("_fromValue"),
            "to": vertical.property("_toValue"),
            "duration": vertical.property("_durationMilliseconds"),
        }
        assert warnings == []
    finally:
        window.close()
        for obj in (window, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
