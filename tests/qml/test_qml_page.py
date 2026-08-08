# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QMLPage public loading-page regressions. QMLPage 公开加载页回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]

QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int lazyRingStyle: Enums.progress.indeterminate_style_fixed_arc
    readonly property int lazyRingSize: Enums.controlSize.navBarHeight
    readonly property int lazyRingSpinDuration: Enums.duration.scroll
    width: 640
    height: 480

    QMLPage {
        objectName: "qmlPage"
        anchors.fill: parent
        text: "Loading page"
        backgroundColor: Enums.transparent
        exitBackgroundColor: Enums.backgroundColor
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_items(root: QQuickItem) -> dict[str, QQuickItem]:
    items = {}
    pending = [root]
    while pending:
        item = pending.pop()
        items[item.objectName()] = item
        pending.extend(item.childItems())
    return items


def test_qml_page_is_public_and_preserves_lazy_progress(qapp):
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
        content = root.findChild(QQuickItem, "qmlPageContent")
        ring = root.findChild(QQuickItem, "qmlPageProgressRing")
        label = root.findChild(QQuickItem, "qmlPageLabel")
        assert page is not None
        assert content is not None
        assert ring is not None
        assert label is not None
        assert page.property("text") == "Loading page"
        assert page.property("running") is True
        assert ring.property("indeterminate") is True
        assert ring.property("indeterminateStyle") == root.property("lazyRingStyle")
        assert ring.property("spinDuration") == root.property("lazyRingSpinDuration")
        assert ring.width() == root.property("lazyRingSize")
        assert ring.height() == root.property("lazyRingSize")
        assert ring.x() + ring.width() / 2 == pytest.approx(
            content.width() / 2, abs=0.5
        )
        assert label.x() + label.width() / 2 == pytest.approx(
            content.width() / 2, abs=0.5
        )
        assert label.y() > ring.y() + ring.height()

        page.setProperty("running", False)
        assert ring.property("indeterminate") is False
        assert ring.property("paused") is True
    finally:
        root.deleteLater()
        engine.deleteLater()


def test_qml_page_finish_uses_reusable_window_close_ripple(qapp):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:qml-page-exit-test.qml"))
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
        content = root.findChild(QQuickItem, "qmlPageContent")
        exit_loader = root.findChild(QQuickItem, "qmlPageExitLoader")
        assert page is not None and content is not None
        assert exit_loader is not None
        assert exit_loader.property("item") is None
        assert QQmlProperty(page, "layer.enabled").read() is False
        assert page.findChild(QQuickItem, "itemCloseRippleFrame") is None

        assert QMetaObject.invokeMethod(page, "finish")
        assert _wait_until(lambda: exit_loader.property("item") is not None)
        visual_items = _visual_items(page)
        ripple = visual_items.get("qmlPageCloseRippleDissolve")
        assert ripple is not None
        assert ripple.property("running") is True
        assert QQmlProperty(page, "layer.enabled").read() is True
        assert QQmlProperty(page, "layer.effect").read() is not None
        assert not any(
            name.startswith("qmlPageGridCell_") for name in visual_items
        )
        _pump(200)
        assert page.property("finishing") is True
        assert 0 < ripple.property("_dissolveProgress") < 1
        assert content.property("opacity") == pytest.approx(1.0)

        _pump(400)
        assert page.property("visible") is False
        assert QQmlProperty(page, "layer.enabled").read() is False
        assert _wait_until(lambda: exit_loader.property("item") is None)
        assert not any(
            name.startswith("qmlPageGridCell_") for name in _visual_items(page)
        )

        assert QMetaObject.invokeMethod(page, "start")
        _pump()
        assert page.property("visible") is True
        assert page.property("finishing") is False
        assert content.property("opacity") == pytest.approx(1.0)
        assert content.property("scale") == pytest.approx(1.0)

        assert QMetaObject.invokeMethod(page, "finish")
        assert _wait_until(lambda: exit_loader.property("item") is not None)
        _pump(100)
        assert QQmlProperty(page, "layer.enabled").read() is True
        assert QMetaObject.invokeMethod(page, "start")
        assert _wait_until(lambda: exit_loader.property("item") is None)
        assert page.property("visible") is True
        assert page.property("finishing") is False
        assert QQmlProperty(page, "layer.enabled").read() is False
    finally:
        root.deleteLater()
        engine.deleteLater()
