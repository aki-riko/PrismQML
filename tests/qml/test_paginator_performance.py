# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Paginator windowing performance regressions. 分页器窗口化性能回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QPointF, QTimer, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QSignalSpy, QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_paginator(total_pages: int, current_page: int, visible_pages: int = 5):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    source = f"""
import QtQuick
import PrismQML

Paginator {{
    readonly property int animationDuration: Enums.duration.medium
    totalPages: {total_pages}
    currentPage: {current_page}
    visiblePages: {visible_pages}
    width: implicitWidth
    height: implicitHeight
}}
"""
    component.setData(source.encode("utf-8"), QUrl("file:///paginator-performance.qml"))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    paginator = component.create(engine.rootContext())
    assert paginator is not None, [error.toString() for error in component.errors()]
    _pump(10)
    return engine, component, paginator, warnings


def _dispose(engine, component, paginator) -> None:
    paginator.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _visual_items(root: QQuickItem) -> list[QQuickItem]:
    result = [root]
    for child in root.childItems():
        result.extend(_visual_items(child))
    return result


def _page_labels(root: QQuickItem) -> dict[int, QQuickItem]:
    labels = {}
    for item in _visual_items(root):
        if not item.metaObject().className().startswith("Label"):
            continue
        text = str(item.property("text"))
        if text.isdigit():
            labels[int(text)] = item
    return labels


def _delegate_positions(root: QQuickItem) -> dict[int, float]:
    return {
        page: label.parentItem().mapToItem(root, QPointF()).x()
        for page, label in _page_labels(root).items()
    }


def _indicator(root: QQuickItem) -> QQuickItem:
    accent = QColor(root.property("accentColor"))
    return next(
        item
        for item in _visual_items(root)
        if item.metaObject().className().startswith("QQuickRectangle")
        and QColor(item.property("color")) == accent
    )


def test_large_paginator_instantiates_only_the_visible_page_window(qapp):
    engine, component, paginator, warnings = _create_paginator(1_000, 500)
    try:
        assert sorted(_page_labels(paginator)) == [498, 499, 500, 501, 502]
        assert len(_visual_items(paginator)) < 100
        assert warnings == []
    finally:
        _dispose(engine, component, paginator)


def test_far_page_jump_preserves_the_full_sliding_path(qapp):
    engine, component, paginator, warnings = _create_paginator(10, 1)
    try:
        duration = paginator.property("animationDuration")
        initial_positions = list(_delegate_positions(paginator).values())
        assert sorted(_page_labels(paginator)) == [1, 2, 3, 4, 5]

        paginator.setProperty("currentPage", 10)
        _pump(1)
        assert sorted(_page_labels(paginator)) == list(range(1, 11))
        _pump(duration // 2)
        assert sorted(_page_labels(paginator)) == list(range(1, 11))
        _pump(duration // 2 + 50)

        final_positions = _delegate_positions(paginator)
        assert sorted(final_positions) == [6, 7, 8, 9, 10]
        assert list(final_positions.values()) == pytest.approx(initial_positions)
        assert _indicator(paginator).mapToItem(paginator, QPointF()).x() == pytest.approx(
            final_positions[10]
        )

        paginator.setProperty("currentPage", 1)
        _pump(1)
        assert sorted(_page_labels(paginator)) == list(range(1, 11))
        _pump(duration + 50)
        assert sorted(_page_labels(paginator)) == [1, 2, 3, 4, 5]
        assert warnings == []
    finally:
        _dispose(engine, component, paginator)


def test_retargeted_slide_settles_only_after_the_last_animation(qapp):
    engine, component, paginator, warnings = _create_paginator(10, 1)
    try:
        duration = paginator.property("animationDuration")
        paginator.setProperty("currentPage", 10)
        _pump(duration // 4)
        paginator.setProperty("currentPage", 4)
        _pump(1)

        assert sorted(_page_labels(paginator)) == list(range(1, 11))
        _pump(duration + 50)
        assert sorted(_page_labels(paginator)) == [2, 3, 4, 5, 6]
        assert warnings == []
    finally:
        _dispose(engine, component, paginator)


def test_runtime_page_count_and_window_size_stay_synchronized(qapp):
    engine, component, paginator, warnings = _create_paginator(10, 5)
    try:
        duration = paginator.property("animationDuration")
        paginator.setProperty("totalPages", 3)
        paginator.setProperty("currentPage", 2)
        _pump(duration + 50)
        assert sorted(_page_labels(paginator)) == [1, 2, 3]

        paginator.setProperty("visiblePages", 3)
        _pump(20)
        assert sorted(_page_labels(paginator)) == [1, 2, 3]

        paginator.setProperty("totalPages", 100)
        paginator.setProperty("currentPage", 50)
        _pump(duration + 50)
        assert sorted(_page_labels(paginator)) == [49, 50, 51]
        assert warnings == []
    finally:
        _dispose(engine, component, paginator)


def test_windowed_page_delegate_keeps_click_routing(qapp):
    engine, component, paginator, warnings = _create_paginator(10, 1)
    window = QQuickWindow()
    window.resize(round(paginator.width()), round(paginator.height()))
    paginator.setParentItem(window.contentItem())
    window.show()
    _pump(20)
    try:
        changed = QSignalSpy(paginator.pageChanged)
        page_three = _page_labels(paginator)[3].parentItem()
        point = page_three.mapToScene(
            QPointF(page_three.width() / 2, page_three.height() / 2)
        ).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
        _pump(10)

        assert paginator.property("currentPage") == 3
        assert changed.count() == 1
        assert warnings == []
    finally:
        paginator.setParentItem(None)
        window.close()
        window.deleteLater()
        _dispose(engine, component, paginator)
