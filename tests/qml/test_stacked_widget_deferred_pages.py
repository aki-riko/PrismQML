# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Inline deferred page API contracts. 内联延迟页面 API 合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlExpression, QQmlEngine

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests/qml/deferred-pages.qml"))


def _pump(milliseconds=50):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(root, source):
    expression = QQmlExpression(QQmlEngine.contextForObject(root), root, source)
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return value[0] if isinstance(value, tuple) else value


def _create(source):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None
    return engine, component, root


def test_deferred_pages_are_created_on_demand_and_released(qapp):
    source = """
import QtQuick
import PrismQML

Item {
    StackedWidget {
        id: stack
        objectName: "deferredStack"
        width: 640
        height: 360
        lazyLoading: true
        animationEnabled: false
        pageRetentionRadius: 0
        deferredPages: [
            Component { Item { objectName: "inline-page-0"; property int marker: 0 } },
            Component { Item { objectName: "inline-page-1"; property int marker: 1 } },
            Component { Item { objectName: "inline-page-2"; property int marker: 2 } }
        ]
    }
}
"""
    engine, component, root = _create(source)
    try:
        stack = root.findChild(QObject, "deferredStack")
        _pump(200)
        assert stack.property("pageModeConflict") is False
        assert stack.property("count") == 3
        assert _evaluate(stack, "_isPageLoaded(0)") is True
        assert _evaluate(stack, "_loaders[1].item") is None

        stack.setProperty("currentIndex", 1)
        _pump(250)
        assert _evaluate(stack, "_loaders[1].item.objectName") == "inline-page-1"
        assert _evaluate(stack, "_loaders[0].item") is None

        stack.setProperty("currentIndex", 0)
        _pump(250)
        assert _evaluate(stack, "_loaders[0].item.objectName") == "inline-page-0"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_deferred_and_source_pages_report_conflict_without_implicit_priority(qapp):
    source = """
import QtQuick
import PrismQML
Item {
    StackedWidget {
        id: stack
        objectName: "conflictStack"
        pageSources: ["file:///missing-page.qml"]
        deferredPages: [Component { Item {} }]
    }
}
"""
    engine, component, root = _create(source)
    try:
        stack = root.findChild(QObject, "conflictStack")
        assert stack.property("pageModeConflict") is True
        assert stack.property("count") == 0
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
