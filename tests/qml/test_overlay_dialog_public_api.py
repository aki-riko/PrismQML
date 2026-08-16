# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Overlay dialog public API and open-hook regressions. 覆盖层公开 API 与打开钩子回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"

SCENE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    readonly property int restoreDelay:
        Enums.duration.medium + Enums.spacing.xl

    function displaceAndReopenMaskedBody() {
        masked.body.anchors.centerIn = undefined
        masked.body.x = 0
        masked.body.y = 0
        masked.open()
    }

    width: 640
    height: 480

    OverlayDialogCore {
        id: overlay
        objectName: "publicOverlay"
        overlayTarget: root
    }

    MaskedDialog {
        id: masked
        objectName: "maskedDialog"
        overlayTarget: root
        body.width: 240
        body.height: 160
    }

    Component.onCompleted: {
        overlay.open()
        masked.open()
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inmemory:/overlay-dialog-public-api.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert isinstance(root, QQuickItem), [error.toString() for error in component.errors()]
    return engine, component, root


def _dispose_scene(engine, component, root):
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_root_module_exports_bodyless_overlay_and_masked_open_hook(qapp):
    engine, component, root = _create_scene()
    try:
        overlay = root.findChild(QQuickItem, "publicOverlay")
        body = root.findChild(QQuickItem, "dialogBody")
        assert overlay is not None
        assert body is not None
        assert overlay.property("_isOpen") is True

        assert QMetaObject.invokeMethod(root, "displaceAndReopenMaskedBody")
        qapp.processEvents()

        assert body.x() == (root.width() - body.width()) / 2
        assert body.y() == (root.height() - body.height()) / 2

        restore_timer = overlay.findChild(
            QObject, "overlayDialogRestoreParentTimer"
        )
        assert restore_timer is not None
        assert restore_timer.parent() is overlay
        assert restore_timer.property("host") == overlay
        assert restore_timer.property("interval") == root.property(
            "restoreDelay"
        )
        assert restore_timer.property("running") is False

        assert QMetaObject.invokeMethod(overlay, "close")
        assert overlay.property("_isOpen") is False
        assert overlay.property("_isClosing") is True
        assert restore_timer.property("running") is True
        _pump(int(root.property("restoreDelay")) + 20)
        assert overlay.property("_isClosing") is False
        assert overlay.isVisible() is False
        assert restore_timer.property("running") is False
    finally:
        _dispose_scene(engine, component, root)


def test_overlay_dialog_anchor_binding_tracks_reparent_and_resize(qapp):
    engine, component, root = _create_scene()
    try:
        overlay = root.findChild(QQuickItem, "publicOverlay")
        alternate_parent = QQuickItem(root)
        alternate_parent.setWidth(512)
        alternate_parent.setHeight(384)

        overlay.setParentItem(alternate_parent)
        qapp.processEvents()

        assert overlay.parentItem() is alternate_parent
        assert overlay.width() == 512
        assert overlay.height() == 384

        alternate_parent.setWidth(560)
        alternate_parent.setHeight(420)
        qapp.processEvents()

        assert overlay.width() == 560
        assert overlay.height() == 420
    finally:
        _dispose_scene(engine, component, root)


def test_dialog_derivatives_extend_the_base_open_hook_without_copying_open():
    masked_source = (QML_ROOT / "controls" / "dialogs" / "MaskedDialog.qml").read_text(encoding="utf-8")
    box_source = (QML_ROOT / "controls" / "dialogs" / "DialogBoxCore.qml").read_text(encoding="utf-8")

    for source in (masked_source, box_source):
        assert "function open()" not in source
        assert "function _prepareOpen()" in source


def test_overlay_dialog_parent_geometry_uses_anchor_binding_without_connections():
    source = (
        QML_ROOT / "controls" / "dialogs" / "OverlayDialogCore.qml"
    ).read_text(encoding="utf-8")

    assert "anchors.fill: parent" in source
    assert "onParentChanged:" not in source
    assert "target: control.parent" not in source
    assert "function onWidthChanged()" not in source
    assert "function onHeightChanged()" not in source
