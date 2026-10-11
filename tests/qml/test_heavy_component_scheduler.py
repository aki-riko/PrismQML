# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Heavy component scheduler runtime contracts. 重型组件调度器运行时合同。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "heavy-component-scheduler.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    property int activationCount: 0
    property string firstActivation: ""
    property bool blockedActivated: false

    Connections {
        target: HeavyComponentScheduler

        function onSlotActivated(slot) {
            root.activationCount += 1
            if (root.firstActivation === "") root.firstActivation = slot.objectName
            if (slot.objectName === "blocked") root.blockedActivated = true
        }
    }

    HeavyComponentSlot {
        id: interactionSlot
        objectName: "interaction"
        width: 20
        height: 20
        scheduled: true
        priority: HeavyComponentScheduler.priority_interaction
        sourceComponent: Component { Rectangle { width: 20; height: 20 } }
    }

    HeavyComponentSlot {
        id: backgroundSlot
        objectName: "background"
        y: 20
        width: 20
        height: 20
        scheduled: true
        priority: HeavyComponentScheduler.priority_background
        sourceComponent: Component { Rectangle { width: 20; height: 20 } }
    }

    HeavyComponentSlot {
        id: blockedSlot
        objectName: "blocked"
        y: 40
        width: 20
        height: 20
        scheduled: true
        pageActive: false
        priority: HeavyComponentScheduler.priority_interaction
        sourceComponent: Component { Rectangle { width: 20; height: 20 } }
    }

    HeavyComponentSlot {
        id: passiveSlot
        objectName: "passive"
        y: 60
        width: 20
        height: 20
        sourceComponent: Component { Rectangle { width: 20; height: 20 } }
    }

    HeavyComponentSlot {
        id: releasableSlot
        objectName: "releasable"
        y: 80
        width: 20
        height: 20
        scheduled: true
        keepAlive: false
        sourceComponent: Component { Rectangle { width: 20; height: 20 } }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root


def test_scheduler_prioritizes_visible_work_and_respects_page_gates(qapp):
    engine, component, root = _create_scene()
    try:
        _pump(70)
        assert root.property("firstActivation") == "interaction"
        assert root.property("activationCount") >= 2
        assert root.property("blockedActivated") is False
        assert root.findChild(QObject, "passive").property("loaded") is False

        blocked = root.findChild(QObject, "blocked")
        blocked.setProperty("pageActive", True)
        _pump(40)
        assert blocked.property("loaded") is True
        assert blocked.property("workActive") is True
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_scheduler_releases_nonretained_content_when_page_deactivates(qapp):
    engine, component, root = _create_scene()
    try:
        _pump(70)
        releasable = root.findChild(QObject, "releasable")
        assert releasable is not None
        assert releasable.property("loaded") is True

        releasable.setProperty("pageActive", False)
        _pump(30)
        assert releasable.property("loaded") is False
        assert releasable.property("workActive") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
