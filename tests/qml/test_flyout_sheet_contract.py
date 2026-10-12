# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FlyoutSheet custom-content API and lifecycle contract. FlyoutSheet 自定义内容 API 与生命周期合同。"""

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    visible: false
    width: 640
    height: 480

    FlyoutSheet {
        id: sheet
        objectName: "flyoutSheet"
        deleteOnClose: false
        contentComponent: Component {
            Item {
                objectName: "customFlyoutContent"
                implicitWidth: 240
                implicitHeight: 120
            }
        }
        Component.onCompleted: open(null)
    }
}
"""


def _pump(ms: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def test_flyout_sheet_loads_custom_content_component_and_closes(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    try:
        engine.loadData(_SOURCE, QUrl("inline"))
        roots = engine.rootObjects()
        assert roots, "FlyoutSheet contract scene failed to load"
        sheet = roots[0].findChild(QQuickWindow, "flyoutSheet")
        assert sheet is not None, "FlyoutSheet instance not found"
        assert sheet.property("contentComponent") is not None

        _pump(120)

        content = next(
            (
                item
                for item in sheet.findChildren(QQuickItem)
                if item.objectName() == "customFlyoutContent"
            ),
            None,
        )
        assert content is not None, "contentComponent was not instantiated by the Loader"
        assert sheet.isVisible()
        assert not any("overrides a member of the base object" in warning for warning in warnings)

        assert QMetaObject.invokeMethod(sheet, "close")
        _pump(20)
        assert not sheet.isVisible()
    finally:
        for obj in engine.rootObjects():
            obj.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
