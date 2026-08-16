# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Widget center timer lifecycle regressions. Widget 居中计时器生命周期回归。"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int tickDuration: Enums.duration.tick

    width: 240
    height: 120

    Widget {
        id: lifecycleWidget
        objectName: "lifecycleWidget"
        width: 120
        height: 60
        centerContent: false

        Rectangle {
            id: centeredChild
            objectName: "centeredChild"
            width: 20
            height: 30
        }
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


def test_widget_center_timer_follows_loader_lifecycle(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("inline:widget-center-timer.qml"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    try:
        widget = root.findChild(QQuickItem, "lifecycleWidget")
        child = root.findChild(QQuickItem, "centeredChild")
        assert widget is not None
        assert child is not None
        loaders = [
            candidate
            for candidate in widget.findChildren(QQuickItem)
            if candidate.metaObject().indexOfProperty("sourceComponent") >= 0
        ]
        assert len(loaders) == 2
        loader = next(candidate for candidate in loaders if not candidate.objectName())
        assert loader.parent() is widget
        assert loader.property("active") is False
        assert widget.findChildren(QObject, "widgetCenterChildrenTimer") == []

        assert widget.setProperty("centerContent", True)
        assert _wait_for(
            lambda: widget.findChild(QObject, "widgetCenterChildrenTimer") is not None
        )
        timer = widget.findChild(QObject, "widgetCenterChildrenTimer")
        assert isinstance(timer, QObject)
        assert timer.objectName() == "widgetCenterChildrenTimer"
        assert timer.parent() is loader
        assert timer.property("host") == widget
        assert timer.property("interval") == root.property("tickDuration")
        assert timer.property("repeat") is False
        assert timer.property("running") is True
        assert _wait_for(
            lambda: child.x() == 50 and child.y() == 15
        )
        assert widget.findChildren(QObject, "widgetCenterChildrenTimer") == [timer]

        assert widget.setProperty("centerContent", False)
        assert _wait_for(
            lambda: widget.findChild(QObject, "widgetCenterChildrenTimer") is None
        )
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        assert not shiboken6.isValid(timer)
        assert widget.findChildren(QObject, "widgetCenterChildrenTimer") == []

        assert widget.setProperty("centerContent", True)
        assert _wait_for(
            lambda: widget.findChild(QObject, "widgetCenterChildrenTimer") is not None
        )
        replacement = widget.findChild(QObject, "widgetCenterChildrenTimer")
        assert replacement.objectName() == "widgetCenterChildrenTimer"
        assert replacement.parent() is loader
        assert replacement.property("host") == widget
        assert widget.findChildren(QObject, "widgetCenterChildrenTimer") == [replacement]
        assert warnings == []
    finally:
        for obj in (root, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
