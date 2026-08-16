# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NotificationAnimator geometry timer regressions. 通知几何计时器回归。"""

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
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "notification-animator-geometry-timer.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "../../prismqml/PrismQML/controls/feedback/Notification" as NotificationLocal

Item {
    id: root

    readonly property real animatorBaseX: animator._baseX
    readonly property bool animatorPositioned: animator._positioned
    readonly property int noDelay: Enums.duration.none
    readonly property int screenMargin: Enums.notification.layout.screenMargin

    function showAnimator() { animator.show() }
    function hideAnimator() { animator.hide() }

    width: 320
    height: 240

    Rectangle {
        id: targetItem
        objectName: "notificationTarget"
        width: 40
        height: 20
        visible: false
    }

    NotificationLocal.NotificationAnimator {
        id: animator
        objectName: "notificationAnimator"
        target: targetItem
        position: Enums.notification.posBottomRight
        parentItem: root
        showDuration: 0
        hideDuration: 0
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


def _expected_right_x(root: QQuickItem, target: QQuickItem) -> float:
    return root.width() - target.width() - root.property("screenMargin")


def test_notification_geometry_timer_coalesces_and_stops_on_hide(qapp):
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
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    try:
        animator = root.findChild(QObject, "notificationAnimator")
        target = root.findChild(QQuickItem, "notificationTarget")
        timer = root.findChild(QObject, "notificationAnimatorGeometryUpdateTimer")
        assert animator is not None
        assert target is not None
        assert timer is not None
        assert timer.parent() is animator
        assert timer.property("host") == animator
        assert timer.property("interval") == root.property("noDelay")
        assert timer.property("repeat") is False
        assert timer.property("running") is False
        assert root.findChildren(
            QObject, "notificationAnimatorGeometryUpdateTimer"
        ) == [timer]

        root.setWidth(360)
        assert timer.property("running") is False
        assert root.property("animatorBaseX") == 0

        assert QMetaObject.invokeMethod(root, "showAnimator")
        assert root.property("animatorPositioned") is True
        assert target.property("visible") is True
        assert root.property("animatorBaseX") == _expected_right_x(root, target)

        root.setWidth(400)
        assert timer.property("running") is True
        root.setWidth(440)
        assert timer.property("running") is True
        assert _wait_for(lambda: timer.property("running") is False)
        assert root.property("animatorBaseX") == _expected_right_x(root, target)

        base_x_before_hide = root.property("animatorBaseX")
        root.setWidth(480)
        assert timer.property("running") is True
        assert QMetaObject.invokeMethod(root, "hideAnimator")
        assert timer.property("running") is False
        _pump()
        assert root.property("animatorBaseX") == base_x_before_hide
        assert root.findChildren(
            QObject, "notificationAnimatorGeometryUpdateTimer"
        ) == [timer]
        assert warnings == []
    finally:
        for obj in (root, component, engine):
            if shiboken6.isValid(obj):
                obj.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()


def test_notification_animator_source_keeps_geometry_timer_external():
    source_path = (
        ROOT
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "feedback"
        / "Notification"
        / "NotificationAnimator.qml"
    )
    helper_path = source_path.parent / "_internal" / (
        "NotificationAnimatorGeometryUpdateTimer.qml"
    )
    source = source_path.read_text(encoding="utf-8")
    helper_source = helper_path.read_text(encoding="utf-8")

    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.NotificationAnimatorGeometryUpdateTimer {" in source
    assert "host: animator" in source
    assert "property Timer _geometryUpdateTimer: Timer {" not in source
    assert "interval: Enums.duration.none" in helper_source
    assert "onTriggered: host.updatePosition()" in helper_source
