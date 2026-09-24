# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vertical orientation contracts. 垂直方向契约回归。

横版行为由既有测试守住（`test_segmented_control_indicator_animation.py`、
`test_pivot_external_binding.py` 等），本文件只验证 `orientation: Qt.Vertical`
新增的主轴行为：单元自上而下堆叠、控件按堆叠高度定尺寸、指示器变成贴左边缘的竖条
并随选中项下滑到位。
"""

import pytest
from pathlib import Path

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


_SCENE_DIR = Path(__file__).resolve().parent

SEGMENTED_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real expectedThickness: Enums.border.thick
    readonly property real expectedPadding: Enums.spacing.xxs * 2
    property int requestedIndex: 1

    width: 360
    height: 360
    visible: true

    SegmentedControl {
        id: segmented
        objectName: "verticalSegmented"
        orientation: Qt.Vertical
        x: 20
        y: 20
        currentIndex: root.requestedIndex
        items: [
            { key: "general", text: "General" },
            { key: "appearance", text: "Appearance" },
            { key: "advanced", text: "Advanced" }
        ]
    }
}
"""

PIVOT_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property real expectedThickness: Enums.border.thick
    readonly property real expectedPadding: Enums.spacing.none
    property int requestedIndex: 1

    width: 360
    height: 360
    visible: true

    Pivot {
        id: pivot
        objectName: "verticalPivot"
        orientation: Qt.Vertical
        x: 20
        y: 20
        currentIndex: root.requestedIndex
        items: [
            { key: "general", text: "General" },
            { key: "appearance", text: "Appearance" },
            { key: "advanced", text: "Advanced" }
        ]
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _visual_descendants(root: QQuickItem):
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.childItems())


def _create_scene(qapp, source: bytes, scene_name: str):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, QUrl.fromLocalFile(str(_SCENE_DIR / scene_name)))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(80)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _parts(window: QQuickWindow, object_name: str):
    control = window.findChild(QQuickItem, object_name)
    assert control is not None
    visual = list(_visual_descendants(control))
    # Indicator geometry lives on the shared animation engine; the public base
    # item itself carries no size. 指示器几何在统一动画引擎上; 公开基类自身无尺寸。
    engines = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("indicatorX") >= 0
        and item.metaObject().indexOfProperty("leadDuration") >= 0
    ]
    delegates = sorted(
        (
            item
            for item in visual
            if item.metaObject().indexOfProperty("selected") >= 0
            and item.metaObject().indexOfProperty("key") >= 0
        ),
        key=lambda item: item.mapToItem(control, QPointF(0, 0)).y(),
    )
    assert len(engines) == 1
    assert len(delegates) == 3
    return control, engines[0], delegates


def _origins(control, delegates):
    return [item.mapToItem(control, QPointF(0, 0)) for item in delegates]


def _assert_stacked(control, window, delegates):
    origins = _origins(control, delegates)
    base = window.property("expectedPadding") / 2

    assert [origin.x() for origin in origins] == pytest.approx(
        [origins[0].x()] * 3, abs=0.01
    )
    assert origins[0].y() == pytest.approx(base, abs=0.01)
    assert origins[1].y() == pytest.approx(base + delegates[0].height(), abs=0.01)
    assert origins[2].y() == pytest.approx(
        base + delegates[0].height() + delegates[1].height(), abs=0.01
    )

    stacked = sum(item.height() for item in delegates)
    assert control.height() == pytest.approx(
        stacked + window.property("expectedPadding"), abs=0.01
    )
    # Cross axis stays content-sized, so the control never grows to the window
    # 副轴按内容定宽, 控件不会撑到窗口宽度
    assert control.width() < window.width() / 2


def _assert_indicator_tracks_selection(control, window, indicator, delegates):
    thickness = float(window.property("expectedThickness"))
    indicator_size = float(control.property("indicatorSize"))

    selected = delegates[1]
    origin = selected.mapToItem(control, QPointF(0, 0))
    assert indicator.property("indicatorWidth") == pytest.approx(
        thickness, abs=0.01
    )
    assert indicator.property("indicatorHeight") == pytest.approx(
        indicator_size, abs=0.01
    )
    assert indicator.property("indicatorX") == pytest.approx(origin.x(), abs=0.01)
    assert indicator.property("indicatorY") == pytest.approx(
        origin.y() + (selected.height() - indicator_size) / 2, abs=0.01
    )

    before_y = indicator.property("indicatorY")
    # Drive the selection through the bound root property so the control's own
    # binding path (not a direct setter call) moves the indicator.
    # 通过绑定的根属性改变选择, 让控件自身的绑定链路驱动指示器。
    window.setProperty("requestedIndex", 2)
    assert _wait_for(lambda: indicator.property("indicatorY") > before_y + 1)
    assert _wait_for(lambda: not indicator.property("running"), timeout_ms=3000)

    last = delegates[2].mapToItem(control, QPointF(0, 0))
    assert indicator.property("indicatorY") == pytest.approx(
        last.y() + (delegates[2].height() - indicator_size) / 2, abs=0.5
    )
    assert indicator.property("indicatorX") == pytest.approx(last.x(), abs=0.5)


def test_vertical_segmented_control_stacks_delegates_on_the_main_axis(qapp):
    """Vertical must stack cells top-to-bottom and size itself to the stack.

    纵向必须自上而下堆叠单元格，并按堆叠高度确定自身尺寸。
    """
    engine, component, window, warnings = _create_scene(
        qapp, SEGMENTED_SCENE, "vertical-segmented-control.qml"
    )
    try:
        control, _indicator, delegates = _parts(window, "verticalSegmented")
        _assert_stacked(control, window, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_segmented_control_moves_indicator_along_the_left_edge(qapp):
    """The indicator is a left-edge bar that slides down with the selection.

    指示器是贴左边缘的竖条，随选中项向下滑动。
    """
    engine, component, window, warnings = _create_scene(
        qapp, SEGMENTED_SCENE, "vertical-segmented-control.qml"
    )
    try:
        control, indicator, delegates = _parts(window, "verticalSegmented")
        _assert_indicator_tracks_selection(control, window, indicator, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_vertical_pivot_stacks_and_keeps_the_indicator_on_the_left_edge(qapp):
    """Pivot must mirror the same vertical contract as the segmented control.

    Pivot 的纵向契约与分段控件一致。
    """
    engine, component, window, warnings = _create_scene(
        qapp, PIVOT_SCENE, "vertical-pivot.qml"
    )
    try:
        control, indicator, delegates = _parts(window, "verticalPivot")
        _assert_stacked(control, window, delegates)
        _assert_indicator_tracks_selection(control, window, indicator, delegates)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
