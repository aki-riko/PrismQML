# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QMLPage public loading-page regressions. QMLPage 公开加载页回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]

QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    width: 640
    height: 480

    QMLPage {
        objectName: "qmlPage"
        anchors.fill: parent
        text: "Loading page"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_qml_page_is_public_and_matches_splash_progress(qapp):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:qml-page-test.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        ring = root.findChild(QQuickItem, "qmlPageProgressRing")
        assert page is not None
        assert ring is not None
        assert page.property("text") == "Loading page"
        assert page.property("running") is True
        assert ring.property("indeterminate") is True
        assert ring.property("indeterminateStyle") == 2
        assert ring.property("spinDuration") == 1000
        assert ring.width() == 20
        assert ring.height() == 20

        page.setProperty("running", False)
        assert ring.property("indeterminate") is False
        assert ring.property("paused") is True
    finally:
        root.deleteLater()
        engine.deleteLater()
