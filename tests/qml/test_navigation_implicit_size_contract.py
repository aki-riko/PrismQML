# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Implicit-size contracts for the navigation family. 导航族的隐式尺寸契约。

既有测试几乎都给控件显式宽度/高度，于是"不给尺寸"这条路径长期没有覆盖：

* 横向 Pivot 曾塌成 44px 并把标签折行（受控 Flow 的隐式尺寸循环依赖）；
* 竖版 TabBar 曾只有 200x44，放不下两行。

本文件把"不给尺寸"的隐式尺寸逐组件锁死：控件必须按内容定尺寸，主轴上的单元必须
排成一行/一列，且不得出现退化尺寸。
"""

import re
import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import configure_qml_environment, register_types


SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: host
    objectName: "host"

    readonly property real inputHeight: Enums.controlSize.inputHeight
    readonly property real segmentedHeight: Enums.controlSize.segmentedHeight
    readonly property real xs: Enums.spacing.xs
    readonly property real xxs: Enums.spacing.xxs
    readonly property real stripWidth: Enums.controlSize.tabBarVerticalWidth
    readonly property real navPanelExpandWidth: Enums.controlSize.navPanelExpandWidth
    readonly property real navBarWidth: Enums.controlSize.navBarWidth

    width: 640
    height: 480
    visible: true

    {body}
}}
"""

PIVOT_BODY = """
    Pivot {{
        objectName: "target"
        orientation: {orientation}
        items: [
            {{ key: "a", text: "Alpha" }}, {{ key: "b", text: "Bravo" }},
            {{ key: "c", text: "Charlie" }}, {{ key: "d", text: "Delta" }}
        ]
    }}
"""

SEGMENTED_BODY = """
    SegmentedControl {{
        objectName: "target"
        orientation: {orientation}
        items: ["Alpha", "Bravo", "Charlie"]
    }}
"""

TAB_BAR_BODY = """
    TabBar {{
        objectName: "target"
        orientation: {orientation}
        tabs: [{{ title: "Alpha" }}, {{ title: "Bravo" }}, {{ title: "Charlie" }}]
    }}
"""

TAB_WIDGET_BODY = """
    TabWidget {{
        objectName: "target"
        orientation: {orientation}
        tabs: [{{ title: "Alpha" }}, {{ title: "Bravo" }}]
    }}
"""

PANEL_BODY = """
    NavigationView {
        objectName: "panel"
        showReturnButton: false
        titleBarHeight: 0
        model: [{ key: "a", text: "Alpha" }, { key: "b", text: "Bravo" }]
    }
    NavigationBar {
        objectName: "bar"
        model: [{ key: "a", text: "Alpha" }, { key: "b", text: "Bravo" }]
    }
    ToggleNavigationBar {
        objectName: "toggle"
        model: [{ key: "a", text: "Alpha" }, { key: "b", text: "Bravo" }]
    }
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 3000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        _pump()
    return predicate()


def _type_name(obj) -> str:
    return re.sub(r"_QMLTYPE_\d+$", "", obj.metaObject().className())


def _visual_descendants(root):
    """Rows created from JS only join the visual parent tree.

    由 JS 创建的行只会挂进视觉父级树。
    """
    pending = list(root.childItems())
    while pending:
        child = pending.pop(0)
        yield child
        pending.extend(child.childItems())


def _create_unsized(qapp, body: str, name: str):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE.format(body=body).encode("utf-8"),
        QUrl.fromLocalFile(f"tests/qml/implicit-{name}.qml"),
    )
    assert _wait_until(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(150)
    return engine, component, window, warnings


def _dispose(engine, component, window, qapp) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _rows(target) -> list:
    return sorted(
        (
            item
            for item in _visual_descendants(target)
            if item.metaObject().indexOfProperty("selected") >= 0
        ),
        key=lambda item: (
            item.mapToItem(target, QPointF(0, 0)).y(),
            item.mapToItem(target, QPointF(0, 0)).x(),
        ),
    )


def _origins(target, rows) -> list:
    return [row.mapToItem(target, QPointF(0, 0)) for row in rows]


def _assert_one_line(target, rows, label: str) -> None:
    origins = _origins(target, rows)
    ys = sorted({round(origin.y(), 1) for origin in origins})
    assert len(ys) == 1, f"{label}: {len(ys)} rows instead of one ({ys})"
    xs = [origin.x() for origin in origins]
    assert xs == sorted(xs), f"{label}: not packed left-to-right ({xs})"


def _assert_one_column(target, rows, label: str) -> None:
    origins = _origins(target, rows)
    xs = sorted({round(origin.x(), 1) for origin in origins})
    assert len(xs) == 1, f"{label}: {len(xs)} columns instead of one ({xs})"
    ys = [origin.y() for origin in origins]
    assert ys == sorted(ys), f"{label}: not stacked top-to-bottom ({ys})"


def test_pivot_implicit_size_matches_its_content(qapp):
    """An un-sized Pivot must take exactly the extent of its cells.

    未指定尺寸的 Pivot 必须正好取各单元的主轴长度。
    """
    for orientation, name in (("Qt.Horizontal", "h"), ("Qt.Vertical", "v")):
        engine, component, window, warnings = _create_unsized(
            qapp, PIVOT_BODY.format(orientation=orientation), f"pivot-{name}"
        )
        try:
            target = window.findChild(QQuickItem, "target")
            rows = _rows(target)
            assert len(rows) == 4
            if orientation == "Qt.Horizontal":
                _assert_one_line(target, rows, "Pivot-H")
                assert target.width() == pytest.approx(
                    sum(row.width() for row in rows), abs=0.5
                )
                assert target.height() == pytest.approx(
                    window.property("inputHeight"), abs=0.5
                )
            else:
                _assert_one_column(target, rows, "Pivot-V")
                assert target.height() == pytest.approx(
                    sum(row.height() for row in rows), abs=0.5
                )
                assert target.width() == pytest.approx(
                    max(row.width() for row in rows), abs=0.5
                )
            assert target.implicitWidth() == pytest.approx(
                target.width(), abs=0.5
            )
            assert warnings == []
        finally:
            _dispose(engine, component, window, qapp)


def test_segmented_control_implicit_size_matches_its_content(qapp):
    """An un-sized SegmentedControl must match its cells plus its own padding.

    未指定尺寸的分段控件必须等于各单元尺寸加自身内边距。
    """
    for orientation, name in (("Qt.Horizontal", "h"), ("Qt.Vertical", "v")):
        engine, component, window, warnings = _create_unsized(
            qapp, SEGMENTED_BODY.format(orientation=orientation),
            f"segmented-{name}",
        )
        try:
            target = window.findChild(QQuickItem, "target")
            rows = _rows(target)
            assert len(rows) == 3
            xs = window.property("xs")
            xxs = window.property("xxs")
            if orientation == "Qt.Horizontal":
                _assert_one_line(target, rows, "Segmented-H")
                assert target.height() == pytest.approx(
                    window.property("segmentedHeight"), abs=0.5
                )
                assert target.width() == pytest.approx(
                    sum(row.width() for row in rows) + xs * 2, abs=0.5
                )
            else:
                _assert_one_column(target, rows, "Segmented-V")
                assert target.height() == pytest.approx(
                    sum(row.height() for row in rows) + xxs * 2, abs=0.5
                )
                assert target.width() == pytest.approx(
                    max(row.width() for row in rows) + xs * 2, abs=0.5
                )
            assert warnings == []
        finally:
            _dispose(engine, component, window, qapp)


def test_tab_bar_implicit_size_keeps_its_strip_shape(qapp):
    """An un-sized TabBar must stay a strip, never a sliver.

    未指定尺寸的 TabBar 必须保持条带形状，不能退化成一条缝。
    """
    engine, component, window, warnings = _create_unsized(
        qapp, TAB_BAR_BODY.format(orientation="Qt.Horizontal"), "tabbar-h"
    )
    try:
        target = window.findChild(QQuickItem, "target")
        rows = _rows(target)
        assert len(rows) == 3
        _assert_one_line(target, rows, "TabBar-H")
        assert target.height() == pytest.approx(
            target.property("_tabBarHeight"), abs=0.5
        )
        assert warnings == []
    finally:
        _dispose(engine, component, window, qapp)

    engine, component, window, warnings = _create_unsized(
        qapp, TAB_BAR_BODY.format(orientation="Qt.Vertical"), "tabbar-v"
    )
    try:
        target = window.findChild(QQuickItem, "target")
        rows = _rows(target)
        assert len(rows) == 3
        _assert_one_column(target, rows, "TabBar-V")
        assert target.width() == pytest.approx(
            window.property("stripWidth"), abs=0.5
        )
        # Rows are row-height, so the natural strip height fits every row
        # 行高即行高, 因此自然高度正好容纳所有行
        assert target.height() == pytest.approx(
            sum(row.height() for row in rows), abs=1.0
        )
        assert target.height() > target.property("_tabHeight"), (
            "vertical strip collapsed to a single row height"
        )
        assert warnings == []
    finally:
        _dispose(engine, component, window, qapp)


def test_tab_widget_implicit_size_keeps_strip_beside_pages(qapp):
    """An un-sized TabWidget must keep the strip outside the page area.

    未指定尺寸的 TabWidget 必须让条带不侵入页面区域。
    """
    for orientation, name in (("Qt.Horizontal", "h"), ("Qt.Vertical", "v")):
        engine, component, window, warnings = _create_unsized(
            qapp, TAB_WIDGET_BODY.format(orientation=orientation),
            f"tabwidget-{name}",
        )
        try:
            target = window.findChild(QQuickItem, "target")
            bar = target.findChild(QQuickItem, "tabBarBg")
            strip = bar.parentItem()
            pages = [
                item for item in target.childItems()
                if _type_name(item).startswith("TabContentPages")
            ]
            assert len(pages) == 1
            page = pages[0]
            assert target.width() > 0 and target.height() > 0
            if orientation == "Qt.Horizontal":
                assert strip.width() == pytest.approx(target.width(), abs=0.5)
                assert page.y() >= strip.height() - 0.5
                assert page.width() == pytest.approx(target.width(), abs=0.5)
            else:
                assert strip.width() == pytest.approx(
                    window.property("stripWidth"), abs=0.5
                )
                assert strip.height() == pytest.approx(
                    target.height(), abs=0.5
                )
                assert page.x() >= strip.width() - 0.5
                assert page.width() == pytest.approx(
                    target.width() - strip.width(), abs=0.5
                )
            assert warnings == []
        finally:
            _dispose(engine, component, window, qapp)


def test_navigation_panels_implicit_width_follows_their_metric(qapp):
    """Panel rails must fall back to their documented widths.

    面板类必须回退到各自的文档宽度。
    """
    engine, component, window, warnings = _create_unsized(
        qapp, PANEL_BODY, "panels"
    )
    try:
        panel = window.findChild(QQuickItem, "panel")
        bar = window.findChild(QQuickItem, "bar")
        toggle = window.findChild(QQuickItem, "toggle")
        for item in (panel, bar, toggle):
            assert item is not None
        assert panel.width() == pytest.approx(
            window.property("navPanelExpandWidth"), abs=0.5
        )
        assert bar.width() == pytest.approx(
            window.property("navBarWidth"), abs=0.5
        )
        # fillWidth (toggle default) makes it span its parent
        # fillWidth（切换栏默认）使其铺满父级
        assert toggle.width() == pytest.approx(window.width(), abs=0.5)
        assert warnings == []
    finally:
        _dispose(engine, component, window, qapp)
