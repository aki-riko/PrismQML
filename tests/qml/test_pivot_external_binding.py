# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Pivot 外部 currentIndex 绑定与指示器同步回归测试。"""

from PySide6.QtCore import QElapsedTimer, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


COMPONENT_READY_TIMEOUT_MS = 2_000
COMPONENT_READY_POLL_MS = 10
STATE_SETTLE_MS = 50


def _create_bound_pivot(engine: QQmlApplicationEngine):
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import PrismQML

Item {
    id: root
    width: 640
    height: 160
    property int requestedIndex: 0

    Pivot {
        objectName: "boundPivot"
        width: 520
        indicatorAnimationEnabled: false
        items: [
            { key: "general", text: "General" },
            { key: "personalization", text: "Personalization" },
            { key: "keyboard", text: "Keyboard" }
        ]
        currentIndex: root.requestedIndex
    }
}
""",
        QUrl("inline:pivot-external-binding"),
    )
    elapsed = QElapsedTimer()
    elapsed.start()
    while component.status() == QQmlComponent.Loading and elapsed.elapsed() < COMPONENT_READY_TIMEOUT_MS:
        QTest.qWait(COMPONENT_READY_POLL_MS)
    assert component.status() == QQmlComponent.Ready, [error.toString() for error in component.errors()]

    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    QTest.qWait(STATE_SETTLE_MS)
    return component, root


def test_external_current_index_binding_keeps_indicator_in_sync(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _create_bound_pivot(engine)
    pivot = root.findChild(QObject, "boundPivot")

    try:
        assert pivot is not None
        assert pivot.property("currentIndex") == 0
        assert pivot.property("_prevIndex") == 0

        assert root.setProperty("requestedIndex", 2)
        QTest.qWait(STATE_SETTLE_MS)

        assert pivot.property("currentIndex") == 2
        assert pivot.property("_prevIndex") == 2
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
