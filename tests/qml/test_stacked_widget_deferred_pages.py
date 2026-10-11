# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Inline deferred page API contracts. 内联延迟页面 API 合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
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


def test_switching_from_deferred_component_to_url_clears_stale_component(qapp, tmp_path):
    page = tmp_path / "url_page.qml"
    page.write_text(
        'import QtQuick\nItem { objectName: "url-page" }\n',
        encoding="utf-8",
    )
    page_url = QUrl.fromLocalFile(str(page)).toString()
    source = f"""
import QtQuick
import PrismQML

Item {{
    function switchToUrl() {{
        stack.pageSources = ["{page_url}"]
        stack.deferredPages = []
    }}

    StackedWidget {{
        id: stack
        objectName: "switchStack"
        width: 320
        height: 200
        lazyLoading: false
        animationEnabled: false
        deferredPages: [Component {{ Item {{ objectName: "inline-page" }} }}]
    }}
}}
"""
    engine, component, root = _create(source)
    try:
        stack = root.findChild(QObject, "switchStack")
        _pump(120)
        assert _evaluate(stack, "currentItem.objectName") == "inline-page"
        assert QMetaObject.invokeMethod(root, "switchToUrl")
        _pump(250)
        assert stack.property("pageModeConflict") is False
        assert _evaluate(stack, "currentItem.objectName") == "url-page"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_replacing_source_while_loading_uses_latest_url(qapp, tmp_path):
    initial_page = tmp_path / "initial_page.qml"
    first_page = tmp_path / "first_page.qml"
    second_page = tmp_path / "second_page.qml"
    initial_page.write_text(
        'import QtQuick\nItem { objectName: "initial-page" }\n',
        encoding="utf-8",
    )
    first_page.write_text(
        'import QtQuick\n'
        'Item {\n'
        '    objectName: "first-page"\n'
        '    Repeater { model: 4000; delegate: Item { width: index; height: index } }\n'
        '}\n',
        encoding="utf-8",
    )
    second_page.write_text(
        'import QtQuick\nItem { objectName: "second-page" }\n',
        encoding="utf-8",
    )
    first_url = QUrl.fromLocalFile(str(first_page)).toString()
    second_url = QUrl.fromLocalFile(str(second_page)).toString()
    initial_url = QUrl.fromLocalFile(str(initial_page)).toString()
    source = f"""
import QtQuick
import PrismQML

Item {{
    property bool loadingObserved: false

    function replaceWhileLoading() {{
        stack.pageSources = ["{first_url}"]
        loadingObserved = stack._loaders[0].status === Loader.Loading
        stack.pageSources = ["{second_url}"]
    }}

    StackedWidget {{
        id: stack
        objectName: "loadingSwitchStack"
        width: 320
        height: 200
        lazyLoading: true
        animationEnabled: false
        pageSources: ["{initial_url}"]
    }}
}}
"""
    engine, component, root = _create(source)
    try:
        stack = root.findChild(QObject, "loadingSwitchStack")
        _pump(150)
        assert _evaluate(stack, "currentItem.objectName") == "initial-page"
        assert QMetaObject.invokeMethod(root, "replaceWhileLoading")
        assert _evaluate(root, "loadingObserved") is True
        _pump(700)
        assert _evaluate(stack, "currentItem.objectName") == "second-page"
        assert _evaluate(stack, "_loaders[0]._loadedSourceText") == second_url
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
