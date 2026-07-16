# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DpiManager public state contract. DpiManager 公开状态合同。"""

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


_EXPECTED_PROPERTIES = {
    "baseDpi",
    "devicePixelRatio",
    "scale",
    "screenDpi",
    "userDpiScale",
}
_REMOVED_PROPERTIES = {
    "borderRadius",
    "borderRadiusLarge",
    "buttonHeight",
    "cardPadding",
    "effectiveScale",
    "fontLarge",
    "fontLargeTitle",
    "fontNormal",
    "fontSmall",
    "fontTitle",
    "inputHeight",
    "spacing2",
    "spacing4",
    "spacing8",
    "spacing12",
    "spacing16",
    "spacing24",
    "spacing32",
}
_PROBE_QML = b"""
import QtQuick
import PrismQML

QtObject {
    property var dpiManager: DpiManager
}
"""


def _wait_until_ready(component):
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]


def test_dpi_manager_exposes_only_unscaled_screen_state(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(_PROBE_QML, QUrl("inline:dpi-manager-contract.qml"))
    _wait_until_ready(component)
    probe = component.create(engine.rootContext())
    assert probe is not None, [error.toString() for error in component.errors()]

    manager = probe.property("dpiManager")
    meta = manager.metaObject()
    properties = {
        meta.property(index).name()
        for index in range(meta.propertyOffset(), meta.propertyCount())
    }
    assert properties == _EXPECTED_PROPERTIES
    assert properties.isdisjoint(_REMOVED_PROPERTIES)
    assert meta.indexOfMethod("dp(QVariant)") == -1
    assert meta.indexOfMethod("sp(QVariant)") == -1
    assert manager.property("baseDpi") == 96
    assert manager.property("screenDpi") > 0
    assert manager.property("scale") >= 1
    assert manager.property("devicePixelRatio") > 0
    assert manager.property("userDpiScale") >= 0

    probe.deleteLater()
    engine.deleteLater()
    qapp.processEvents()
