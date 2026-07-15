# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TabWidget indicator animation regressions. TabWidget 指示器动画回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
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
    str(ROOT / "tests" / "qml" / "tab-widget-indicator-animation.qml")
)
def _scene_source(initial_index: int = 0) -> bytes:
    return f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: root
    property int requestedIndex: {initial_index}
    property int tabClickedCount: 0
    property int reorderedCount: 0
    property int reorderedFrom: -1
    property int reorderedTo: -1
    property var eventOrder: []
    readonly property real borderThin: Enums.border.thin

    function widenAnimatedLayout() {{
        var next = tabs.tabs.slice()
        next[0] = Object.assign({{}}, next[0], {{ title: "A very wide leading tab" }})
        next[tabs.currentIndex] = Object.assign(
            {{}}, next[tabs.currentIndex],
            {{ title: "A very wide current tab used during animation" }})
        tabs.tabs = next
    }}

    function removeCurrentTab() {{ tabs.removeTab(tabs.currentIndex) }}
    function clearTabs() {{ tabs.clear() }}
    function addWideTab() {{ tabs.addTab("A newly added wide tab", "", page) }}
    function applyReorder(from, to) {{
        var next = tabs.tabs.slice()
        var moved = next.splice(from, 1)[0]
        next.splice(to, 0, moved)
        tabs.tabs = next
    }}

    onRequestedIndexChanged: tabs.setCurrentIndex(requestedIndex)

    width: 760
    height: 360
    visible: true

    Component {{
        id: page
        Rectangle {{ color: Enums.cardColor }}
    }}

    TabWidget {{
        id: tabs
        objectName: "tabWidget"
        x: 20
        y: 20
        width: 720
        height: 300
        currentIndex: root.requestedIndex
        movable: true
        scrollable: true
        tabs: [
            {{ title: "Alpha", content: page }},
            {{ title: "Bravo", content: page }},
            {{ title: "Charlie", content: page }},
            {{ title: "Delta", content: page }},
            {{ title: "Echo", content: page }},
            {{ title: "Foxtrot", content: page }}
        ]
        onTabClicked: root.tabClickedCount++
        onCurrentChanged: function(index) {{ root.eventOrder = root.eventOrder.concat(["current:" + tabs.tabText(index)]) }}
        onTabsReordered: function(from, to) {{
            root.eventOrder = root.eventOrder.concat(["reorder:" + tabs.tabText(from)])
            root.reorderedCount++
            root.reorderedFrom = from
            root.reorderedTo = to
            root.applyReorder(from, to)
        }}
    }}
}}
""".encode("utf-8")
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


def _object_descendants(root: QObject):
    pending = list(root.children())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.children())


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
def tab_scene(qapp):
    scene = _create_scene()
    try:
        yield scene
    finally:
        _dispose_scene(*scene[:3])


def _parts(window: QQuickWindow):
    tab = window.findChild(QQuickItem, "tabWidget")
    assert tab is not None
    visual = list(_visual_descendants(tab))
    indicators = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("_currentTabKey") >= 0
    ]
    flickables = [item for item in visual if item.inherits("QQuickFlickable")]
    delegates = sorted(
        (
            item
            for item in visual
            if item.metaObject().indexOfProperty("visualOffsetX") >= 0
            and item.metaObject().indexOfProperty("selected") >= 0
        ),
        key=lambda item: item.x(),
    )
    assert len(indicators) == 1
    assert len(flickables) == 1
    assert delegates
    indicator = indicators[0]
    engines = [
        child
        for child in _object_descendants(indicator)
        if child.metaObject().indexOfProperty("indicatorX") >= 0
        and child.metaObject().indexOfProperty("leadDuration") >= 0
    ]
    assert len(engines) == 1
    return tab, indicator, engines[0], flickables[0], delegates


def _edge_inset(indicator, flickable, delegate) -> float:
    return indicator.x() - flickable.x() - delegate.x() + flickable.property("contentX")


def _expected_x(flickable, delegate, inset: float) -> float:
    return flickable.x() + delegate.x() - flickable.property("contentX") + inset


def _strictly_between(value: float, start: float, end: float) -> bool:
    lower, upper = sorted((start, end))
    return lower + 0.5 < value < upper - 0.5


def _sample_switch(window, engine, indicator, target_index: int):
    start_x = indicator.x()
    window.setProperty("requestedIndex", target_index)
    samples = [(0, indicator.x())]
    _pump(20)
    samples.append((20, indicator.x()))
    _pump(60)
    samples.append((80, indicator.x()))
    _pump(80)
    samples.append((160, indicator.x()))
    assert engine.property("running")
    return start_x, samples


def test_external_set_current_index_has_real_intermediate_frames(tab_scene):
    _engine, _component, window, warnings = tab_scene
    _tab, indicator, animation, flickable, delegates = _parts(window)
    inset = _edge_inset(indicator, flickable, delegates[0])
    target_x = _expected_x(flickable, delegates[4], inset)

    start_x, samples = _sample_switch(window, animation, indicator, 4)

    assert samples[0][1] == pytest.approx(start_x, abs=0.5)
    assert samples[0][1] != pytest.approx(target_x, abs=0.5)
    assert all(
        _strictly_between(value, start_x, target_x) for _time, value in samples[1:]
    ), samples
    assert _wait_for(lambda: not animation.property("running"))
    assert indicator.x() == pytest.approx(target_x, abs=0.5)
    assert indicator.width() == pytest.approx(delegates[4].width(), abs=0.5)
    assert warnings == []


def test_mouse_click_switch_has_real_intermediate_frames(tab_scene):
    _engine, _component, window, warnings = tab_scene
    _tab, indicator, animation, flickable, delegates = _parts(window)
    inset = _edge_inset(indicator, flickable, delegates[0])
    target = delegates[2]
    target_x = _expected_x(flickable, target, inset)
    point = target.mapToItem(
        window.contentItem(), QPointF(target.width() / 2, target.height() / 2)
    )
    start_x = indicator.x()

    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    samples = [(0, indicator.x())]
    _pump(20)
    samples.append((20, indicator.x()))
    _pump(60)
    samples.append((80, indicator.x()))
    _pump(80)
    samples.append((160, indicator.x()))

    assert window.property("tabClickedCount") == 1
    assert samples[0][1] == pytest.approx(start_x, abs=0.5)
    assert all(
        _strictly_between(value, start_x, target_x) for _time, value in samples[1:]
    ), samples
    assert animation.property("running")
    assert _wait_for(lambda: not animation.property("running"))
    assert indicator.x() == pytest.approx(target_x, abs=0.5)
    assert warnings == []


def test_interrupted_switch_continues_from_current_engine_frame(tab_scene):
    _engine, _component, window, warnings = tab_scene
    _tab, indicator, animation, flickable, delegates = _parts(window)
    inset = _edge_inset(indicator, flickable, delegates[0])
    reverse_target_x = _expected_x(flickable, delegates[1], inset)
    window.setProperty("requestedIndex", 4)
    _pump(80)
    interrupted_x = indicator.x()
    assert animation.property("running")

    window.setProperty("requestedIndex", 1)
    immediate_x = indicator.x()
    _pump(20)
    resumed_x = indicator.x()

    assert immediate_x == pytest.approx(interrupted_x, abs=0.5)
    assert _strictly_between(resumed_x, reverse_target_x, interrupted_x)
    assert animation.property("running")
    assert _wait_for(lambda: not animation.property("running"))
    assert indicator.x() == pytest.approx(reverse_target_x, abs=0.5)
    assert warnings == []


def test_scroll_and_indicator_animation_run_together(tab_scene):
    _engine, _component, window, warnings = tab_scene
    tab, indicator, animation, flickable, delegates = _parts(window)
    inset = _edge_inset(indicator, flickable, delegates[0])
    tab.setWidth(300)
    _pump(30)
    start_engine_x = animation.property("indicatorX")

    window.setProperty("requestedIndex", 5)
    _pump(80)

    assert flickable.property("contentX") > 0
    assert animation.property("indicatorX") > start_engine_x
    assert animation.property("indicatorX") < delegates[5].x()
    expected_visible_x = (
        flickable.x()
        + animation.property("indicatorX")
        - flickable.property("contentX")
        + inset
    )
    assert indicator.x() == pytest.approx(expected_visible_x, abs=0.5)
    assert animation.property("running")
    assert _wait_for(lambda: not animation.property("running"))
    assert _wait_for(
        lambda: indicator.x()
        == pytest.approx(_expected_x(flickable, delegates[5], inset), abs=0.5)
    )
    assert warnings == []


def test_layout_changes_retarget_running_animation(tab_scene):
    _engine, _component, window, warnings = tab_scene
    _tab, indicator, animation, flickable, delegates = _parts(window)
    inset = _edge_inset(indicator, flickable, delegates[0])
    window.setProperty("requestedIndex", 4)
    _pump(80)
    before_x = animation.property("indicatorX")
    before_width = animation.property("indicatorWidth")

    assert QMetaObject.invokeMethod(window, "widenAnimatedLayout")
    _pump(20)
    _tab, indicator, animation, flickable, delegates = _parts(window)

    assert animation.property("running")
    assert animation.property("indicatorX") >= before_x - 1
    assert animation.property("indicatorWidth") >= before_width - 1
    assert _wait_for(lambda: not animation.property("running"))
    assert animation.property("indicatorX") == pytest.approx(delegates[4].x(), abs=0.5)
    assert animation.property("indicatorWidth") == pytest.approx(
        delegates[4].width(), abs=0.5
    )
    assert indicator.x() == pytest.approx(
        _expected_x(flickable, delegates[4], inset), abs=0.5
    )
    assert warnings == []


def test_dynamic_remove_clear_and_readd_keep_geometry_valid(tab_scene):
    _engine, _component, window, warnings = tab_scene
    tab, indicator, animation, flickable, _delegates = _parts(window)
    window.setProperty("requestedIndex", 5)
    assert _wait_for(lambda: not animation.property("running"))

    assert QMetaObject.invokeMethod(window, "removeCurrentTab")
    assert _wait_for(lambda: tab.property("currentIndex") == 4)
    assert _wait_for(lambda: not animation.property("running"))
    _tab, indicator, animation, flickable, delegates = _parts(window)
    assert animation.property("indicatorX") == pytest.approx(delegates[4].x(), abs=0.5)
    assert animation.property("indicatorWidth") == pytest.approx(
        delegates[4].width(), abs=0.5
    )

    assert QMetaObject.invokeMethod(window, "clearTabs")
    _pump(30)
    assert not indicator.isVisible()
    assert not animation.property("running")
    assert QMetaObject.invokeMethod(window, "addWideTab")
    _pump(50)
    visual = list(_visual_descendants(tab))
    delegates = [
        item
        for item in visual
        if item.metaObject().indexOfProperty("visualOffsetX") >= 0
        and item.metaObject().indexOfProperty("selected") >= 0
    ]
    assert len(delegates) == 1
    assert indicator.isVisible()
    assert animation.property("indicatorWidth") == pytest.approx(
        delegates[0].width(), abs=0.5
    )
    assert animation.property("indicatorWidth") > 60
    assert warnings == []


def test_nonzero_initial_index_has_no_wrong_flash(qapp):
    engine, component, window, warnings = _create_scene(initial_index=3, settle_ms=0)
    try:
        tab, indicator, animation, flickable, delegates = _parts(window)
        inset = window.property("borderThin")
        if indicator.isVisible():
            assert indicator.x() == pytest.approx(
                _expected_x(flickable, delegates[3], inset), abs=0.5
            )
        _pump(80)
        assert not animation.property("running")
        assert indicator.x() == pytest.approx(
            _expected_x(flickable, delegates[3], inset), abs=0.5
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_real_drag_reorders_model_and_resettles_indicator(tab_scene):
    _engine, _component, window, warnings = tab_scene
    tab, indicator, animation, flickable, delegates = _parts(window)
    start = delegates[0].mapToItem(
        window.contentItem(), QPointF(delegates[0].width() / 2, delegates[0].height() / 2)
    )
    target = delegates[1].mapToItem(
        window.contentItem(), QPointF(delegates[1].width() / 2, delegates[1].height() / 2)
    )
    start_point = QPoint(round(start.x()), round(start.y()))
    target_point = QPoint(round(target.x()), round(target.y()))
    middle_point = QPoint(
        round((start.x() + target.x()) / 2), round((start.y() + target.y()) / 2)
    )

    QTest.mouseMove(window, start_point)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start_point
    )
    QTest.mouseMove(window, middle_point, 10)
    QTest.mouseMove(window, target_point, 10)
    assert tab.property("_dragging")
    assert not indicator.isVisible()
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, target_point
    )

    assert _wait_for(lambda: window.property("reorderedCount") == 1)
    assert window.property("reorderedFrom") == 0
    assert window.property("reorderedTo") == 1
    assert window.property("tabClickedCount") == 0
    assert window.property("eventOrder").toVariant() == [
        "reorder:Alpha",
        "current:Alpha",
    ]
    assert _wait_for(lambda: not animation.property("running"))
    tab, indicator, animation, flickable, delegates = _parts(window)
    assert tab.property("currentIndex") == 1
    assert indicator.isVisible()
    assert indicator.x() == pytest.approx(
        _expected_x(flickable, delegates[1], window.property("borderThin")), abs=0.5
    )
    assert animation.property("indicatorWidth") == pytest.approx(
        delegates[1].width(), abs=0.5
    )
    assert warnings == []


def test_pending_indicator_sync_is_cancelled_when_window_is_destroyed(qapp):
    engine, component, window, warnings = _create_scene()
    window.setProperty("requestedIndex", 4)
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(30)
    try:
        assert warnings == []
    finally:
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump(20)
