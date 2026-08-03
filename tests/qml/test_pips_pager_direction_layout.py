# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PipsPager direction layout regressions. 分页指示器方向布局回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "FlipView"
    / "PipsPagerCore.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "pips-pager-direction-layout.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/data/FlipView" as FlipViewControls

Window {
    id: window

    property int clickedIndex: -1
    readonly property int fastDuration: Enums.duration.fast
    readonly property int mediumDuration: Enums.duration.medium

    width: 420
    height: 240
    visible: true
    color: Enums.backgroundColor

    FlipViewControls.PipsPager {
        id: pager
        objectName: "pager"
        x: 120
        y: 80
        count: 7
        maxVisible: 5
        currentIndex: 0

        onIndexClicked: (index) => window.clickedIndex = index
    }
}
"""


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _visible_pip_delegates(pager: QQuickItem, vertical: bool) -> list[QQuickItem]:
    delegates = []
    pending = list(pager.childItems())
    while pending:
        item = pending.pop()
        if not item.isVisible():
            continue
        children = item.childItems()
        child_types = [child.metaObject().className() for child in children]
        if any("Rectangle" in name for name in child_types) and any(
            "MouseArea" in name for name in child_types
        ):
            delegates.append(item)
            continue
        pending.extend(children)
    return sorted(delegates, key=lambda item: item.y() if vertical else item.x())


def _dot(delegate: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in delegate.childItems()
        if "Rectangle" in child.metaObject().className()
    ]
    assert len(matches) == 1
    return matches[0]


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    center = item.mapToScene(item.boundingRect().center())
    return QPoint(round(center.x()), round(center.y()))


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_pips_pager_preserves_animation_and_interaction_across_direction(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    pager = window.findChild(QQuickItem, "pager")
    assert pager is not None
    fast_duration = int(window.property("fastDuration"))
    medium_duration = int(window.property("mediumDuration"))
    normal_diameter = float(pager.property("_normalDiameter"))
    active_diameter = float(pager.property("_activeDiameter"))
    cell_size = float(pager.property("_cellSize"))
    QTest.qWait(max(fast_duration, medium_duration) + 30)

    try:
        horizontal = _visible_pip_delegates(pager, vertical=False)
        assert len(horizontal) == 7
        assert _dot(horizontal[0]).width() == pytest.approx(active_diameter)
        assert all(
            _dot(delegate).width() == pytest.approx(normal_diameter)
            for delegate in horizontal[1:]
        )
        assert all(
            delegate.y() + delegate.height() / 2 == pytest.approx(pager.height() / 2)
            for delegate in horizontal
        )

        pager.setProperty("currentIndex", 4)
        QTest.qWait(20)
        pager.setProperty("orientation", Qt.Orientation.Vertical.value)
        QCoreApplication.processEvents()

        vertical = _visible_pip_delegates(pager, vertical=True)
        assert len(vertical) == 7
        old_width = _dot(vertical[0]).width()
        new_width = _dot(vertical[4]).width()
        scroll_target = 2 * cell_size
        mid_scroll_y = vertical[0].mapToItem(pager, QPointF()).y()
        assert normal_diameter < old_width < active_diameter
        assert normal_diameter < new_width < active_diameter
        assert -scroll_target < mid_scroll_y < 0
        assert all(
            delegate.x() + delegate.width() / 2 == pytest.approx(pager.width() / 2)
            for delegate in vertical
        )

        QTest.qWait(max(fast_duration, medium_duration) + 30)
        assert _dot(vertical[0]).width() == pytest.approx(normal_diameter)
        assert _dot(vertical[4]).width() == pytest.approx(active_diameter)
        assert vertical[0].mapToItem(pager, QPointF()).y() == pytest.approx(
            -scroll_target
        )

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=_point_for(window, vertical[2]),
        )
        assert pager.property("currentIndex") == 2
        assert window.property("clickedIndex") == 2

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_pips_pager_uses_one_shared_direction_delegate_set():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert source.count("Repeater {") == 1
    assert "Row {" not in source
    assert "Column {" not in source
    assert "property real _animatedScrollOffset: _scrollOffset" in source
