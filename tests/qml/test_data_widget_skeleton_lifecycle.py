# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DataWidget skeleton lifecycle regressions. 数据组件骨架屏生命周期回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    width: 360
    height: 260
    visible: true

    Fluent.ListView {
        objectName: "widget"
        x: 20
        y: 20
        width: 320
        height: 220
        animated: false
        loading: false
        model: []
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_items(root: QQuickItem) -> list[QQuickItem]:
    items = []
    pending = [root]
    while pending:
        item = pending.pop()
        items.append(item)
        pending.extend(item.childItems())
    return items


def _skeletons(widget: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in _visual_items(widget)
        if item.metaObject().className().startswith("Skeleton")
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "data-widget-skeleton-lifecycle.qml")
        ),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    widget = window.findChild(QQuickItem, "widget")
    assert widget is not None
    _pump(60)
    return engine, component, window, widget, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_data_widget_skeletons_preserve_loading_geometry_across_cycles(qapp):
    engine, component, window, widget, warnings = _create_scene()
    try:
        assert all(not skeleton.isVisible() for skeleton in _skeletons(widget))

        widget.setProperty("loading", True)
        assert _wait_for(lambda: 3 <= len(_skeletons(widget)) <= 5)
        first = _skeletons(widget)
        assert all(skeleton.isVisible() for skeleton in first)
        assert all(skeleton.property("loading") is True for skeleton in first)
        first_geometry = [
            (skeleton.x(), skeleton.y(), skeleton.width(), skeleton.height())
            for skeleton in first
        ]
        assert all(width > 0 and height > 0 for _, _, width, height in first_geometry)

        widget.setProperty("loading", False)
        assert _wait_for(
            lambda: all(not skeleton.isVisible() for skeleton in _skeletons(widget))
        )
        widget.setProperty("loading", True)
        assert _wait_for(lambda: len(_skeletons(widget)) == len(first_geometry))
        second = _skeletons(widget)
        second_geometry = [
            (skeleton.x(), skeleton.y(), skeleton.width(), skeleton.height())
            for skeleton in second
        ]
        assert second_geometry == pytest.approx(first_geometry)
        assert all(skeleton.isVisible() for skeleton in second)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
