# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget lazy switch races. StackedWidget 懒加载切页竞态回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_stack(tmp_path: Path, engine: QQmlApplicationEngine):
    page_urls = []
    for index, color in enumerate(("#dd4444", "#44dd44", "#4444dd")):
        page = tmp_path / f"page_{index}.qml"
        page.write_text(
            "import QtQuick\n"
            f'Rectangle {{ objectName: "page{index}"; color: "{color}"; '
            "anchors.fill: parent; MouseArea { anchors.fill: parent } }\n",
            encoding="utf-8",
        )
        page_urls.append(QUrl.fromLocalFile(str(page)).toString())

    quoted_urls = ", ".join(f'"{url}"' for url in page_urls)
    source = f"""
import QtQuick
import PrismQML

Item {{
    width: 320
    height: 180

    StackedWidget {{
        id: stack
        objectName: "stack"
        anchors.fill: parent
        lazyLoading: true
        animationType: Enums.animation.popup
        animationDuration: Enums.duration.slow
        pageSources: [{quoted_urls}]
    }}
}}
""".encode("utf-8")
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:stacked-widget-lazy-switch-race"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [
        error.toString() for error in component.errors()
    ]
    return component, root, root.findChild(QObject, "stack")


def _dispose(engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    _pump()


def test_retargeting_to_visible_page_cancels_old_lazy_request(qapp, tmp_path):
    """返回当前页后，旧目标不得在后台抢回显示权。"""
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component, root, stack = _create_stack(tmp_path, engine)
    try:
        _pump(500)
        initial_loaders = stack.property("_loaders").toVariant()
        assert initial_loaders[0].property("item") is not None
        assert stack.property("_displayIndex") == 0
        stack.setProperty("currentIndex", 1)
        _pump(20)
        stack.setProperty("currentIndex", 0)

        assert _wait_for(lambda: stack.property("_displayIndex") == 0)
        _pump(500)

        loaders = stack.property("_loaders").toVariant()
        visible_indexes = [
            index for index, loader in enumerate(loaders) if loader.property("visible")
        ]
        assert stack.property("currentIndex") == 0
        assert stack.property("_displayIndex") == 0
        assert visible_indexes == [0]
    finally:
        _dispose(engine, component, root)
