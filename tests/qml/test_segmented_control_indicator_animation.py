# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SegmentedControl indicator animation regressions. 分段控件指示器动画回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "segmented-control-indicator-animation.qml")
)
SCENE_TEMPLATE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    property int requestedIndex: __INITIAL_INDEX__
    property int itemClickedCount: 0
    property int lastClickedIndex: -1

    function widenLeadingItem() {
        var next = segmented.items.slice()
        next[0] = Object.assign(
            {}, next[0],
            { text: "A much wider leading segment used during animation" })
        segmented.items = next
    }
    function clearItems() { segmented.items = [] }
    function addSingleWideItem() {
        segmented.items = [{ key: "single", text: "A newly added wide segment" }]
        segmented.currentIndex = 0
    }

    width: 620
    height: 120
    visible: true
    onRequestedIndexChanged: segmented.setCurrentIndex(requestedIndex)

    SegmentedControl {
        id: segmented
        objectName: "segmentedControl"
        x: 20
        y: 20
        width: 580
        height: 40
        currentIndex: __INITIAL_INDEX__
        items: [
            { key: "alpha", text: "Alpha" },
            { key: "bravo", text: "Bravo wide" },
            { key: "charlie", text: "Charlie" },
            { key: "delta", text: "Delta wider" },
            { key: "echo", text: "Echo" }
        ]
        onItemClicked: function(index, byUser) {
            if (!byUser) return
            root.itemClickedCount++
            root.lastClickedIndex = index
        }
    }
}
"""


def _scene_source(initial_index: int = 0) -> bytes:
    return SCENE_TEMPLATE.replace(b"__INITIAL_INDEX__", str(initial_index).encode("ascii"))


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


def _create_scene(initial_index: int = 0, settle_ms: int = 80):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(_scene_source(initial_index), SCENE_URL)
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
    window.requestActivate()
    if settle_ms:
        _pump(settle_ms)
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


@pytest.fixture
def segmented_scene(qapp):
    scene = _create_scene()
    try:
        yield scene
    finally:
        _dispose_scene(*scene[:3])


def _parts(window: QQuickWindow):
    control = window.findChild(QQuickItem, "segmentedControl")
    assert control is not None
    visual = list(_visual_descendants(control))
    indicators = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("_initialized") >= 0
        and item.metaObject().indexOfProperty("animationEnabled") >= 0
    ]
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
        key=lambda item: item.mapToItem(control, QPointF(0, 0)).x(),
    )
    assert len(indicators) == 1
    assert len(engines) == 1
    assert delegates
    return control, indicators[0], engines[0], delegates


def _expected_x(control, delegate) -> float:
    item_origin = delegate.mapToItem(control, QPointF(0, 0))
    return item_origin.x() + (delegate.width() - control.property("indicatorSize")) / 2


def _strictly_between(value: float, start: float, end: float) -> bool:
    lower, upper = sorted((start, end))
    return lower + 0.5 < value < upper - 0.5


def _samples(engine):
    values = [(0, float(engine.property("indicatorX")))]
    for elapsed in (20, 80, 160):
        _pump(elapsed - values[-1][0])
        values.append((elapsed, float(engine.property("indicatorX"))))
    return values


def test_external_set_current_index_has_real_intermediate_frames(segmented_scene):
    _engine, _component, window, warnings = segmented_scene
    control, _indicator, animation, delegates = _parts(window)
    start_x = float(animation.property("indicatorX"))
    target_x = _expected_x(control, delegates[4])

    assert window.setProperty("requestedIndex", 4)
    samples = _samples(animation)

    assert samples[0][1] == pytest.approx(start_x, abs=0.5)
    assert all(_strictly_between(value, start_x, target_x) for _, value in samples[1:]), samples
    assert animation.property("running")
    assert _wait_for(lambda: not animation.property("running"))
    assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
    assert warnings == []


def test_mouse_click_switch_has_real_intermediate_frames(segmented_scene):
    _engine, _component, window, warnings = segmented_scene
    control, _indicator, animation, delegates = _parts(window)
    start_x = float(animation.property("indicatorX"))
    target = delegates[2]
    target_x = _expected_x(control, target)
    point = target.mapToItem(
        window.contentItem(), QPointF(target.width() / 2, target.height() / 2)
    )

    click_point = QPoint(round(point.x()), round(point.y()))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=click_point)
    samples = _samples(animation)

    assert window.property("itemClickedCount") == 1
    assert window.property("lastClickedIndex") == 2
    assert samples[0][1] == pytest.approx(start_x, abs=0.5)
    assert all(_strictly_between(value, start_x, target_x) for _, value in samples[1:]), samples
    assert _wait_for(lambda: not animation.property("running"))
    assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
    assert warnings == []


def test_preceding_item_width_change_retargets_running_animation(segmented_scene):
    _engine, _component, window, warnings = segmented_scene
    assert window.setProperty("requestedIndex", 3)
    _pump(80)
    control, _indicator, animation, delegates = _parts(window)
    before_x = float(animation.property("indicatorX"))
    old_target_x = _expected_x(control, delegates[3])

    assert QMetaObject.invokeMethod(window, "widenLeadingItem")
    _pump(20)
    control, _indicator, animation, delegates = _parts(window)
    target_x = _expected_x(control, delegates[3])
    current_x = float(animation.property("indicatorX"))

    assert abs(target_x - old_target_x) > 1
    assert animation.property("running")
    assert _strictly_between(current_x, before_x, target_x)
    assert current_x != pytest.approx(target_x, abs=0.5)
    assert _wait_for(lambda: not animation.property("running"))
    assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
    assert warnings == []


def test_dynamic_clear_and_readd_restores_valid_geometry(segmented_scene):
    _engine, _component, window, warnings = segmented_scene
    _control, indicator, animation, _delegates = _parts(window)
    assert QMetaObject.invokeMethod(window, "clearItems")
    _pump(30)
    assert not indicator.isVisible()
    assert not animation.property("running")

    assert QMetaObject.invokeMethod(window, "addSingleWideItem")
    _pump(80)
    control, indicator, animation, delegates = _parts(window)
    target_x = _expected_x(control, delegates[0])

    assert indicator.isVisible()
    assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
    assert warnings == []


def test_nonzero_initial_index_has_no_wrong_flash(qapp):
    engine, component, window, warnings = _create_scene(initial_index=3, settle_ms=0)
    try:
        control, indicator, animation, delegates = _parts(window)
        target_x = _expected_x(control, delegates[3])
        if indicator.property("_initialized"):
            assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
        _pump(80)
        assert not animation.property("running")
        assert animation.property("indicatorX") == pytest.approx(target_x, abs=0.5)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
