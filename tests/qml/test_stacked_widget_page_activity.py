# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget opt-in page activity contracts. StackedWidget 页面活动状态契约。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "stacked-widget-page-activity.qml")
)


def _pump(milliseconds: int = 40) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(root, expression: str):
    expression_object = QQmlExpression(
        QQmlEngine.contextForObject(root), root, expression
    )
    value = expression_object.evaluate()
    assert not expression_object.hasError(), expression_object.error().toString()
    return value[0] if isinstance(value, tuple) else value


def _create_component(engine, source: str):
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None
    return component, root


def _meta_property(item, name: str) -> bool:
    return item.metaObject().indexOfProperty(name) >= 0


def test_direct_pages_only_receive_declared_activity_properties(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    source = """
import QtQuick
import PrismQML

Item {
    function showPlain() { stack.currentIndex = 2 }
    function showPageActive() { stack.currentIndex = 1 }

    StackedWidget {
        id: stack
        objectName: "directActivityStack"
        width: 400
        height: 240
        animationEnabled: false

        Item {
            objectName: "schedulerPage"
            property bool schedulerActive: true
        }
        Item {
            objectName: "pageActivePage"
            property bool pageActive: true
        }
        Item {
            objectName: "plainPage"
        }
    }
}
"""
    component, root = _create_component(engine, source)
    try:
        stack = root.findChild(QObject, "directActivityStack")
        assert stack is not None
        _pump()

        first = stack.itemAt(0)
        second = stack.itemAt(1)
        plain = stack.itemAt(2)
        assert first is not None and second is not None and plain is not None
        assert _meta_property(first, "schedulerActive")
        assert _meta_property(second, "pageActive")
        assert not _meta_property(plain, "schedulerActive")
        assert not _meta_property(plain, "pageActive")
        assert bool(first.property("schedulerActive")) is True
        assert bool(second.property("pageActive")) is False

        assert QMetaObject.invokeMethod(root, "showPlain")
        _pump()
        assert bool(first.property("schedulerActive")) is False
        assert bool(second.property("pageActive")) is False
        assert not _meta_property(plain, "schedulerActive")
        assert not _meta_property(plain, "pageActive")

        assert QMetaObject.invokeMethod(root, "showPageActive")
        _pump()
        assert bool(first.property("schedulerActive")) is False
        assert bool(second.property("pageActive")) is True
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_source_pages_only_receive_declared_activity_properties(qapp, tmp_path):
    pages = []
    page_sources = (
        "Item { objectName: \"sourceScheduler\"; property bool schedulerActive: true }",
        "Item { objectName: \"sourcePageActive\"; property bool pageActive: true }",
        "Item { objectName: \"sourcePlain\" }",
    )
    for index, page_body in enumerate(page_sources):
        page = tmp_path / f"activity_page_{index}.qml"
        page.write_text("import QtQuick\n" + page_body + "\n", encoding="utf-8")
        pages.append(QUrl.fromLocalFile(str(page)).toString())

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    quoted_pages = ", ".join(f'"{page}"' for page in pages)
    source = f"""
import QtQuick
import PrismQML

Item {{
    function showPageActive() {{ stack.currentIndex = 1 }}
    function showPlain() {{ stack.currentIndex = 2 }}

    StackedWidget {{
        id: stack
        objectName: "sourceActivityStack"
        width: 400
        height: 240
        animationEnabled: false
        lazyLoading: false
        pageSources: [{quoted_pages}]
    }}
}}
"""
    component, root = _create_component(engine, source)
    try:
        stack = root.findChild(QObject, "sourceActivityStack")
        assert stack is not None
        _pump(120)

        first = _evaluate(root, "stack.itemAt(0).item")
        second = _evaluate(root, "stack.itemAt(1).item")
        plain = _evaluate(root, "stack.itemAt(2).item")
        assert first is not None and second is not None and plain is not None
        assert bool(first.property("schedulerActive")) is True
        assert bool(second.property("pageActive")) is False
        assert not _meta_property(plain, "schedulerActive")
        assert not _meta_property(plain, "pageActive")

        assert QMetaObject.invokeMethod(root, "showPageActive")
        _pump()
        assert bool(first.property("schedulerActive")) is False
        assert bool(second.property("pageActive")) is True

        assert QMetaObject.invokeMethod(root, "showPlain")
        _pump()
        assert bool(first.property("schedulerActive")) is False
        assert bool(second.property("pageActive")) is False
        assert not _meta_property(plain, "schedulerActive")
        assert not _meta_property(plain, "pageActive")
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
