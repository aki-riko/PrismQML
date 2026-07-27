# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Overlay dialog public API and open-hook regressions. 覆盖层公开 API 与打开钩子回归。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QTimer, QUrl
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


def _create_scene():
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inmemory:/overlay-dialog-public-api.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
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
    finally:
        _dispose_scene(engine, component, root)


def test_dialog_derivatives_extend_the_base_open_hook_without_copying_open():
    masked_source = (QML_ROOT / "controls" / "dialogs" / "MaskedDialog.qml").read_text(encoding="utf-8")
    box_source = (QML_ROOT / "controls" / "dialogs" / "DialogBoxCore.qml").read_text(encoding="utf-8")

    for source in (masked_source, box_source):
        assert "function open()" not in source
        assert "function _prepareOpen()" in source
