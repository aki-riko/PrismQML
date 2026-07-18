# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TreeView asynchronous model regressions. TreeView 异步模型回归。"""

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.core.incubation import install_incubation_controller


SCENE_URL = QUrl("inline:tree-view-async-model.qml")
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 300
    height: 380

    Loader {
        anchors.fill: parent
        asynchronous: true

        sourceComponent: Component {
            Item {
                TreeView {
                    objectName: "treeView"
                    width: 280
                    height: 360
                    model: [
                        {
                            text: "Root",
                            expanded: true,
                            children: [{ text: "Leaf" }]
                        }
                    ]
                }
            }
        }
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def test_tree_view_async_loader_tracks_internal_list_model(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    install_incubation_controller(engine)

    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]

    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]

    try:
        tree = None
        for _ in range(100):
            tree = root.findChild(QObject, "treeView")
            if tree is not None:
                break
            _pump()
        assert tree is not None

        for _ in range(100):
            if tree.property("itemCount") == 2:
                break
            _pump()

        assert tree.count() == 2
        assert tree.property("itemCount") == 2
        delegates = [
            item
            for item in _descendants(tree)
            if item.metaObject().indexOfProperty("itemText") >= 0
        ]
        assert delegates
        assert delegates[0].property("itemText") == "Root"
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
        engine.deleteLater()
        _pump(1)
