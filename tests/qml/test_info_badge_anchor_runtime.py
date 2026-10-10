# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""InfoBadge host anchoring runtime contracts. InfoBadge 宿主锚定运行时合同。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "info-badge-anchor.qml")
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 400
    height: 300
    visible: false

    readonly property real offsetToken: Enums.spacing.xs

    function destroySecondHost() { secondHost.destroy() }

    function moveHost() {
        host.x = 140
        host.y = 110
    }

    function resizeHost() {
        host.width = 160
        host.height = 90
    }

    Rectangle {
        id: host
        objectName: "host"
        x: 100
        y: 80
        width: 120
        height: 60
        color: Enums.cardColor
    }

    Rectangle {
        id: secondHost
        objectName: "secondHost"
        x: 260
        y: 180
        width: 80
        height: 40
        color: Enums.cardColor
    }

    Badge {
        objectName: "badgeTopLeft"
        target: host
        anchorPosition: Enums.position.top_left
        count: 3
    }

    Badge {
        objectName: "badgeTopRight"
        target: host
        anchorPosition: Enums.position.top_right
        count: 3
    }

    Badge {
        objectName: "badgeBottomLeft"
        target: host
        anchorPosition: Enums.position.bottom_left
        count: 3
    }

    Badge {
        objectName: "badgeBottomRight"
        target: host
        anchorPosition: Enums.position.bottom_right
        count: 3
    }

    Badge {
        objectName: "badgeBaseline"
        x: 12
        y: 14
        count: 3
    }

    Badge {
        objectName: "badgeRetarget"
        target: host
        anchorPosition: Enums.position.top_right
        count: 3
    }

    Badge {
        objectName: "badgeDestructible"
        target: secondHost
        anchorPosition: Enums.position.bottom_right
        count: 3
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


def _item(window, name) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, name
    return item


def _top_left_in_scene(window, item: QQuickItem):
    return item.mapToItem(window.contentItem(), QPointF(0.0, 0.0))


def test_anchor_positions_place_badge_on_host_corners(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        host = _item(window, "host")
        offset = window.property("offsetToken")
        host_x = host.x()
        host_y = host.y()
        host_right = host_x + host.width()
        host_bottom = host_y + host.height()

        expected = {
            "badgeTopLeft": (host_x - offset, host_y - offset),
            "badgeTopRight": (host_right, host_y - offset),
            "badgeBottomLeft": (host_x - offset, host_bottom),
            "badgeBottomRight": (host_right, host_bottom),
        }
        for name, (right_edge, bottom_edge) in expected.items():
            badge = _item(window, name)
            origin = _top_left_in_scene(window, badge)
            if name.endswith("Left"):
                assert origin.x() == host_x - offset
            else:
                assert origin.x() + badge.width() == right_edge + offset
            if "Top" in name:
                assert origin.y() == host_y - offset
            else:
                assert origin.y() + badge.height() == bottom_edge + offset
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_badge_without_target_keeps_declarative_geometry(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        badge = _item(window, "badgeBaseline")
        assert badge.property("target") is None
        assert badge.x() == 12
        assert badge.y() == 14
        assert badge.parentItem() is window.contentItem()

        # Changing the anchor props must not move a badge without a target.
        # 改变锚定属性不得移动没有 target 的徽章。
        badge.setProperty("anchorPosition", 0)
        badge.setProperty("anchorOffset", 40.0)
        _pump(30)
        assert badge.x() == 12
        assert badge.y() == 14
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_anchor_follows_target_moves_and_resizes(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        badge = _item(window, "badgeTopRight")
        offset = window.property("offsetToken")

        assert QMetaObject.invokeMethod(window, "moveHost")
        _pump(30)
        host = _item(window, "host")
        origin = _top_left_in_scene(window, badge)
        assert origin.x() + badge.width() == host.x() + host.width() + offset
        assert origin.y() == host.y() - offset

        assert QMetaObject.invokeMethod(window, "resizeHost")
        _pump(30)
        origin = _top_left_in_scene(window, badge)
        assert origin.x() + badge.width() == host.x() + host.width() + offset
        assert origin.y() == host.y() - offset
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_clearing_target_restores_declarative_geometry(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        badge = _item(window, "badgeRetarget")
        host = _item(window, "host")
        assert badge.x() + badge.width() == host.x() + host.width() + window.property(
            "offsetToken"
        )

        badge.setProperty("target", None)
        _pump(30)
        assert badge.property("target") is None
        assert badge.x() == 0
        assert badge.y() == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_destroyed_target_is_safe(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        badge = _item(window, "badgeDestructible")
        assert badge.property("target") is not None

        assert QMetaObject.invokeMethod(window, "destroySecondHost")
        _pump(60)
        assert badge.property("target") is None
        assert badge.x() == 0
        assert badge.y() == 0
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
