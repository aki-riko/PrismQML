# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery RefreshContainer demo contract. 图库下拉刷新示例契约回归。

示例卡不只是"能创建"：它必须真实承载宿主契约 —— 容器发出
refreshRequested、示例自己的宿主逻辑结束刷新并把内容归位。
"""

import time
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types
from prismqml.python.core.incubation import install_default_incubation_controller


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "examples" / "pages" / "ContainerPage.qml"


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _descendants(item: QQuickItem):
    """Walk the visual tree; visual children are not QObject children."""
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _load_page():
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    install_default_incubation_controller(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(SOURCE_PATH)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert isinstance(root, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root, warnings


def _dispose(engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_gallery_container_page_documents_the_pull_refresh_host_contract():
    """The demo must show the host-owned refreshing contract in its source.

    示例源码必须体现"宿主负责结束刷新"的契约。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert 'title: "RefreshContainer"' in source
    assert "id: refreshDemo" in source
    assert "onRefreshRequested: refreshDemoTimer.restart()" in source
    assert "id: refreshDemoTimer" in source
    assert "onTriggered: refreshDemo.refreshing = false" in source
    # The container owns `refreshing`; a demo binding would break the contract.
    # 容器自己持有 refreshing, 示例一旦绑定就会破坏契约。
    assert "refreshing: refreshDemo" not in source
    assert "requestRefresh()" in source


def test_gallery_refresh_demo_completes_a_refresh_cycle(qapp):
    """Programmatic refresh fires once, then the demo host clears it.

    编程式刷新只发一次, 随后由示例宿主自行结束并归位。
    """
    engine, component, root, warnings = _load_page()
    window = QQuickWindow()
    window.resize(1_200, 800)
    root.setParentItem(window.contentItem())
    root.setSize(window.size())
    window.show()
    try:
        container = root.findChild(QObject, "refreshDemo")
        assert container is not None

        hits: list[str] = []
        container.refreshRequested.connect(lambda: hits.append("requested"))

        container.requestRefresh()
        _pump(60)
        assert hits == ["requested"]
        assert container.property("refreshing") is True

        # A refresh in flight is never re-requested 刷新中不得重复触发
        container.requestRefresh()
        _pump(60)
        assert hits == ["requested"]

        # The demo's own host timer ends the refresh 示例宿主的定时器结束刷新
        assert _wait_for(
            lambda: container.property("refreshing") is False,
            timeout_ms=3_000,
        ), "the demo never finished its simulated refresh"
        assert _wait_for(
            lambda: abs(float(container.property("_offset"))) < 0.5
        ), "content did not settle back after the refresh finished"
        assert container.property("indicatorVisible") is False

        # The card really is wired to a scroll surface 卡片确实接到了滚动面
        assert container.findChild(QObject, "refreshDemoList") is not None
        surfaces = [
            item
            for item in _descendants(container)
            if item.metaObject().indexOfProperty("contentY") >= 0
        ]
        assert surfaces, "no scroll surface inside the demo container"
        assert warnings == []
    finally:
        window.close()
        window.deleteLater()
        _dispose(engine, component, root)
