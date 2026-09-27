# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Caution status semantic contract. 黄色谨慎状态语义契约。"""

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine

from prismqml import Theme, register_types, setTheme


SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int cautionLevel: Enums.statusLevel.caution
    readonly property string cautionName: Enums.statusLevel.cautionStr
    readonly property color cautionToken: Enums.statusLevel.cautionColor
    readonly property color cautionByLevel: Enums.statusLevel.getColorByLevel(cautionLevel)
    readonly property color cautionByName: Enums.statusLevel.getColor(cautionName)
    readonly property color cautionBackground: Enums.statusLevel.getBgColor(cautionName)
    readonly property color warningToken: Enums.statusLevel.warningColor
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_caution_is_a_distinct_yellow_status(qapp):
    setTheme(Theme.LIGHT)
    engine = QQmlApplicationEngine()
    engine.addImportPath("prismqml")
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("status-level-caution.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]

    assert root.property("cautionLevel") == 6
    assert root.property("cautionName") == "caution"
    caution = QColor(root.property("cautionToken"))
    assert caution == QColor(root.property("cautionByLevel"))
    assert caution == QColor(root.property("cautionByName"))
    assert caution != QColor(root.property("warningToken"))
    assert QColor(root.property("cautionBackground")).isValid()
