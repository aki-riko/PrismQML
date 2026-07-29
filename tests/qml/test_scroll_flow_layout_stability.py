# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Responsive FlowLayout scrollbar stability. 响应式流布局滚动条稳定性。"""

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl("inline:scroll-flow-layout-stability.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML as Fluent

Item {
    id: root

    readonly property real expectedInset:
        Fluent.Enums.controlSize.scrollBarWidth + Fluent.Enums.spacing.xs
    readonly property real viewportInset:
        area.flickableItem
            ? area.flickableItem.parent.width - area.flickableItem.width : -1
    readonly property real flowWidth: flowDemo.width
    readonly property real flowHeight: flowDemo.implicitHeight
    property bool tracking: false
    property int flowWidthChanges: 0
    property int flowHeightChanges: 0

    function beginTracking() {
        flowWidthChanges = 0
        flowHeightChanges = 0
        tracking = true
    }

    function stopTracking() {
        tracking = false
    }

    width: 500
    height: 500

    Fluent.ScrollArea {
        id: area
        anchors.fill: parent
        anchors.margins: Fluent.Enums.spacing.m

        Fluent.FlowLayout {
            id: flowDemo
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.s
            rowSpacing: Fluent.Enums.spacing.s
            mode: Fluent.Enums.flow.default_
            columnCount: 6

            onWidthChanged: {
                if (root.tracking) root.flowWidthChanges++
            }
            onImplicitHeightChanged: {
                if (root.tracking) root.flowHeightChanges++
            }

            Repeater {
                model: 50
                Rectangle {
                    width: 40 + (index % 7) * 12
                    height: 30 + (index * 17 % 80)
                }
            }
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def test_responsive_flow_layout_settles_after_scrollbar_gutter(qapp):
    """Scrollbar measurement must converge after responsive relayout. 滚动条测量必须收敛。"""
    configure_qml_environment()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        expected_inset = float(root.property("expectedInset"))
        assert _wait_for(
            lambda: float(root.property("viewportInset")) == expected_inset
        )
        _pump(300)
        root.beginTracking()
        _pump(600)
        root.stopTracking()

        assert float(root.property("viewportInset")) == expected_inset
        assert float(root.property("flowWidth")) == 440
        assert float(root.property("flowHeight")) == 821
        assert int(root.property("flowWidthChanges")) == 0
        assert int(root.property("flowHeightChanges")) == 0
        assert warnings == []
        assert [
            window
            for window in QGuiApplication.topLevelWindows()
            if window.isVisible()
            and not any(window is existing for existing in windows_before)
        ] == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
