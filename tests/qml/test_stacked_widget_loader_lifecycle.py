# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget Loader lifecycle regressions. StackedWidget Loader 生命周期回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
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
