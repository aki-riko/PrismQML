# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget Loader lifecycle regressions. StackedWidget Loader 生命周期回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine, QQmlExpression

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "stacked-widget-loader-lifecycle.qml")
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(root, expression: str):
    qml_expression = QQmlExpression(QQmlEngine.contextForObject(root), root, expression)
    value = qml_expression.evaluate()
    assert not qml_expression.hasError(), qml_expression.error().toString()
    return value[0] if isinstance(value, tuple) else value


def test_shrinking_page_sources_drops_destroyed_loader_references(qapp, tmp_path):
    page_urls = []
    for index in range(3):
        page = tmp_path / f"page_{index}.qml"
        page.write_text("import QtQuick\nItem {}\n", encoding="utf-8")
        page_urls.append(QUrl.fromLocalFile(str(page)).toString())

    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    quoted_urls = ", ".join(f'"{url}"' for url in page_urls)
    source = f"""
import QtQuick
import PrismQML

Item {{
    width: 400
    height: 240

    function shrinkAndSwitch() {{
        stack.pageSources = [{quoted_urls.split(', ')[0]}, {quoted_urls.split(', ')[1]}]
        stack.currentIndex = 1
    }}

    StackedWidget {{
        id: stack
        anchors.fill: parent
        lazyLoading: false
        pageSources: [{quoted_urls}]
    }}
}}
""".encode("utf-8")
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    try:
        assert root is not None
        _pump(60)
        assert QMetaObject.invokeMethod(root, "shrinkAndSwitch")
        _pump(60)
        assert _evaluate(root, "stack._loaders.length") == 2
        assert not any("Cannot assign to non-existent property" in warning for warning in warnings), warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_dynamic_stack_push_pop_preserves_lazy_loading_and_initial_properties(qapp, tmp_path):
    page_urls = []
    for index in range(2):
        page = tmp_path / f"dynamic_page_{index}.qml"
        page.write_text(
            'import QtQuick\n'
            'Item {\n'
            '    property string marker: "unset"\n'
            '    objectName: "dynamic-" + marker\n'
            '}\n',
            encoding="utf-8",
        )
        page_urls.append(QUrl.fromLocalFile(str(page)).toString())

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    source = f"""
import QtQuick
import PrismQML

Item {{
    width: 400
    height: 240

    function pushSecond() {{
        stack.push("{page_urls[1]}", {{ marker: "second" }})
    }}

    function popCurrent() {{
        stack.pop()
    }}

    StackedWidget {{
        id: stack
        objectName: "dynamicStack"
        anchors.fill: parent
        lazyLoading: true
        dynamicStack: true
        pageSources: ["{page_urls[0]}"]
        pageProperties: [{{ marker: "first" }}]
    }}
}}
""".encode("utf-8")
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    try:
        assert root is not None
        _pump(700)
        stack = root.findChild(QObject, "dynamicStack")
        assert stack is not None
        assert _evaluate(root, "stack.depth") == 1
        assert _evaluate(root, "stack.currentWidget.item.objectName") == "dynamic-first"

        assert QMetaObject.invokeMethod(root, "pushSecond")
        _pump(1000)
        assert _evaluate(root, "stack.depth") == 2
        assert _evaluate(root, "stack.currentIndex") == 1
        assert _evaluate(root, "stack.currentWidget.item.objectName") == "dynamic-second"

        assert QMetaObject.invokeMethod(root, "popCurrent")
        _pump(700)
        assert _evaluate(root, "stack.depth") == 1
        assert _evaluate(root, "stack.currentIndex") == 0
        assert _evaluate(root, "stack.currentWidget.item.objectName") == "dynamic-first"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_source_mode_current_widget_is_null_until_loader_is_registered(qapp, tmp_path):
    page = tmp_path / "initial_page.qml"
    page.write_text("import QtQuick\nItem {}\n", encoding="utf-8")
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    source = f"""
import QtQuick
import PrismQML
Item {{
    StackedWidget {{
        id: stack
        width: 200
        height: 120
        lazyLoading: true
        pageSources: ["{QUrl.fromLocalFile(str(page)).toString()}"]
    }}
}}
""".encode("utf-8")
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    try:
        assert root is not None
        _pump(700)
        assert not any("Unable to assign [undefined] to QQuickItem" in warning for warning in warnings), warnings
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
