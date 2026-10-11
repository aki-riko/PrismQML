# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Opt-in source page retention contracts. source 页面驻留合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlExpression, QQmlEngine

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests/qml/stacked-widget-page-retention.qml")
)


def _pump(milliseconds: int = 40) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(root, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(root), root, source)
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return value[0] if isinstance(value, tuple) else value


def _create_scene(page_urls, retention_radius):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    quoted = ", ".join(f'"{url}"' for url in page_urls)
    source = f"""
import QtQuick
import PrismQML
Item {{
    StackedWidget {{
        id: stack
        objectName: "retentionStack"
        width: 640
        height: 360
        lazyLoading: true
        animationEnabled: false
        pageRetentionRadius: {retention_radius}
        pageSources: [{quoted}]
    }}
}}
""".encode("utf-8")
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None
    return engine, component, root


def _page_files(tmp_path):
    urls = []
    for index in range(4):
        page = tmp_path / f"retention_page_{index}.qml"
        page.write_text(
            "import QtQuick\n"
            f'Item {{ objectName: "retention-page-{index}"; property int marker: {index} }}\n',
            encoding="utf-8",
        )
        urls.append(QUrl.fromLocalFile(str(page)).toString())
    return urls


def test_retention_radius_releases_far_source_pages_and_reloads_on_return(qapp, tmp_path):
    engine, component, root = _create_scene(_page_files(tmp_path), 0)
    try:
        stack = root.findChild(QObject, "retentionStack")
        assert stack is not None
        _pump(300)
        assert _evaluate(stack, "_isPageLoaded(0)") is True
        stack.setProperty("currentIndex", 1)
        _pump(300)
        assert _evaluate(stack, "_isPageLoaded(1)") is True
        assert _evaluate(stack, "_loaders[0].active") is False
        assert _evaluate(stack, "_isPageLoaded(0)") is False
        assert _evaluate(stack, "_loaders[0].item") is None

        stack.setProperty("currentIndex", 0)
        _pump(300)
        assert _evaluate(stack, "_isPageLoaded(0)") is True
        assert _evaluate(stack, "_loaders[0].item.objectName") == "retention-page-0"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_default_retention_keeps_existing_lazy_page_resident(qapp, tmp_path):
    engine, component, root = _create_scene(_page_files(tmp_path), -1)
    try:
        stack = root.findChild(QObject, "retentionStack")
        _pump(300)
        stack.setProperty("currentIndex", 1)
        _pump(300)
        assert _evaluate(stack, "_isPageLoaded(0)") is True
        assert _evaluate(stack, "_loaders[0].item.objectName") == "retention-page-0"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


def test_retention_keeps_previous_page_during_transition(qapp, tmp_path):
    engine, component, root = _create_scene(_page_files(tmp_path), 0)
    try:
        stack = root.findChild(QObject, "retentionStack")
        stack.setProperty("animationEnabled", True)
        _pump(300)
        stack.setProperty("currentIndex", 1)
        _pump(40)
        assert _evaluate(stack, "_loaders[0].item") is not None
        _pump(500)
        assert _evaluate(stack, "_loaders[0].item") is None
        assert _evaluate(stack, "_loaders[1].item") is not None
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
