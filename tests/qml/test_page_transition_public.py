# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public PageTransition contracts. 公开 PageTransition 合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "controls" / "navigation" / "PageTransition.qml"
QMldir_PATH = ROOT / "prismqml" / "PrismQML" / "qmldir"
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "page-transition-public.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    id: root

    property int noneType: Enums.animation.none
    property int circleType: Enums.animation.lazy_circle
    property int customType: Enums.animation.custom
    property int collapseStartedCount: 0
    property int collapseFinishedCount: 0
    property int expandStartedCount: 0
    property int expandFinishedCount: 0
    property int customCollapseStartedCount: 0
    property int customCollapseFinishedCount: 0
    property int customExpandStartedCount: 0
    property int customExpandFinishedCount: 0

    width: 320
    height: 180

    Rectangle {
        id: source
        objectName: "source"
        anchors.fill: parent
        color: "#3487eb"
    }

    PageTransition {
        id: noneTransition
        objectName: "noneTransition"
        animationType: Enums.animation.none
        onCollapseStarted: root.collapseStartedCount += 1
        onCollapseFinished: root.collapseFinishedCount += 1
        onExpandStarted: root.expandStartedCount += 1
        onExpandFinished: root.expandFinishedCount += 1
    }

    PageTransition {
        id: circleTransition
        objectName: "circleTransition"
        animationType: Enums.animation.lazy_circle
    }

    PageTransition {
        id: customTransition
        objectName: "customTransition"
        animationType: Enums.animation.custom
        onCollapseStarted: root.customCollapseStartedCount += 1
        onCollapseFinished: root.customCollapseFinishedCount += 1
        onExpandStarted: root.customExpandStartedCount += 1
        onExpandFinished: root.customExpandFinishedCount += 1
        customAnimation: Component {
            Item {
                property bool active: false
                property bool running: false
                property bool collapsing: false
                property bool collapsed: false
                property real progress: 0
                signal collapseStarted()
                signal expandStarted()
                signal collapseFinished()
                signal expandFinished()
                function collapse(item) {
                    collapsing = true
                    active = true
                    running = true
                    item.visible = false
                    collapseStarted()
                    progress = 1
                    collapsed = true
                    running = false
                    active = false
                    collapseFinished()
                    return true
                }
                function expand(item) {
                    collapsing = false
                    active = true
                    running = true
                    expandStarted()
                    progress = 1
                    collapsed = false
                    item.visible = true
                    running = false
                    active = false
                    expandFinished()
                    return true
                }
                function stop() {
                    active = false
                    running = false
                    collapsed = false
                }
            }
        }
    }

    PageTransition {
        id: invalidTransition
        objectName: "invalidTransition"
        animationType: Enums.animation.custom
        customAnimation: Component { Item {} }
    }

    Component.onCompleted: {
        noneTransition.collapse(source)
        noneTransition.expand(source)
        customTransition.collapse(source)
        customTransition.expand(source)
        invalidTransition.collapse(source)
    }
}
"""


def _pump(milliseconds=20):
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
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root


def test_page_transition_is_public_and_supports_builtin_and_custom_contracts(qapp):
    engine, component, root = _create_scene()
    try:
        assert SOURCE_PATH.is_file()
        assert "PageTransition controls/navigation/PageTransition.qml" in QMldir_PATH.read_text(
            encoding="utf-8"
        )
        assert root.property("noneType") == 0
        assert root.property("circleType") == 7
        assert root.property("customType") == 8
        assert root.property("collapseStartedCount") == 1
        assert root.property("collapseFinishedCount") == 1
        assert root.property("expandStartedCount") == 1
        assert root.property("expandFinishedCount") == 1
        assert root.property("customCollapseStartedCount") == 1
        assert root.property("customCollapseFinishedCount") == 1
        assert root.property("customExpandStartedCount") == 1
        assert root.property("customExpandFinishedCount") == 1
        source = root.findChild(QQuickItem, "source")
        assert source is not None
        assert source.property("visible") is False
        custom = root.findChild(QQuickItem, "customTransition")
        assert custom.property("customAnimationContractValid") is True
        circle = root.findChild(QQuickItem, "circleTransition")
        assert circle.property("customAnimationContractValid") is True
        assert circle.findChild(QQuickItem, "qmlPageCircleTransition") is not None
        invalid = root.findChild(QQuickItem, "invalidTransition")
        assert invalid.property("customAnimationContractValid") is False
        assert invalid.property("collapsed") is True
        assert QMetaObject.invokeMethod(invalid, "stop")
        assert invalid.property("collapsed") is False
        assert source.property("visible") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)


def test_page_transition_source_declares_explicit_custom_contract():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert 'property int animationType: Enums.animation.lazy_circle' in source
    assert 'property Component customAnimation: null' in source
    assert 'Enums.animation.none' in source
    assert 'Enums.animation.custom' in source
    assert '"collapse", "expand", "stop"' in source
    assert '"active", "running", "collapsing", "collapsed", "progress"' in source
    assert 'signal collapseStarted()' in source
    assert 'signal expandFinished()' in source
