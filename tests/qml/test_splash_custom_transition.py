# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SplashScreen transition injection contracts. SplashScreen 过渡注入合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "splash-custom-transition.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root
    property int finishedCount: 0

    Rectangle {
        id: page
        objectName: "page"
        anchors.fill: parent
        color: "#3487eb"
    }

    SplashScreen {
        id: splash
        objectName: "splash"
        showTitleBar: false
        showProgress: false
        exitAnimationType: Enums.animation.custom
        exitAnimation: Component {
            Item {
                property bool active: false
                property bool running: false
                property bool collapsing: false
                property bool collapsed: false
                property real progress: 0
                signal collapseStarted()
                signal collapseFinished()
                signal expandStarted()
                signal expandFinished()
                function collapse(item) { item.visible = false; return true }
                function expand(item) {
                    expandStarted()
                    active = true
                    running = true
                    progress = 1
                    item.visible = true
                    running = false
                    active = false
                    expandFinished()
                    return true
                }
                function stop() { active = false; running = false }
            }
        }
        onFinished: root.finishedCount += 1
    }
}
"""


def _pump(milliseconds=20):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_splashscreen_accepts_custom_exit_component(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None
    try:
        splash = root.findChild(QQuickItem, "splash")
        assert splash is not None
        assert splash.property("exitAnimationType") == 8
        assert QMetaObject.invokeMethod(splash, "finish")
        _pump()
        assert root.property("finishedCount") == 1
        assert splash.property("visible") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)
