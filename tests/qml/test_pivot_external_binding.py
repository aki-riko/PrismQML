# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Pivot 外部 currentIndex 绑定与指示器同步回归测试。"""

import pytest
from PySide6.QtCore import QElapsedTimer, QObject, QPointF, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from prismqml import register_types


COMPONENT_READY_TIMEOUT_MS = 2_000
COMPONENT_READY_POLL_MS = 10
STATE_SETTLE_MS = 50


def _create_bound_pivot(engine: QQmlApplicationEngine):
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import PrismQML

Item {
    id: root
    width: 640
    height: 160
    property int requestedIndex: 0
    readonly property int expectedIndicatorSyncInterval: Enums.duration.tick
    property var pivotItems: [
        { key: "general", text: "General" },
        { key: "personalization", text: "Personalization" },
        { key: "keyboard", text: "Keyboard" }
    ]

    Pivot {
        objectName: "boundPivot"
        width: 520
        indicatorAnimationEnabled: false
        items: root.pivotItems
        currentIndex: root.requestedIndex
    }
}
""",
        QUrl("inline:pivot-external-binding"),
    )
    elapsed = QElapsedTimer()
    elapsed.start()
    while component.status() == QQmlComponent.Loading and elapsed.elapsed() < COMPONENT_READY_TIMEOUT_MS:
        QTest.qWait(COMPONENT_READY_POLL_MS)
    assert component.status() == QQmlComponent.Ready, [error.toString() for error in component.errors()]

    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    QTest.qWait(STATE_SETTLE_MS)
    return component, root


def _visual_descendants(root: QQuickItem):
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.childItems())


def _pivot_parts(root: QQuickItem):
    pivot = root.findChild(QQuickItem, "boundPivot")
    assert pivot is not None
    visual = list(_visual_descendants(pivot))
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
        key=lambda item: item.mapToItem(pivot, QPointF(0, 0)).x(),
    )
    assert len(indicators) == 1
    assert len(engines) == 1
    return pivot, indicators[0], engines[0], delegates


def _expected_x(pivot: QQuickItem, delegate: QQuickItem) -> float:
    origin = delegate.mapToItem(pivot, QPointF(0, 0))
    return origin.x() + (delegate.width() - pivot.property("indicatorSize")) / 2


def _wait_until(predicate, timeout_ms: int = 1_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        QTest.qWait(COMPONENT_READY_POLL_MS)
        elapsed += COMPONENT_READY_POLL_MS
    return predicate()


def test_external_current_index_binding_keeps_indicator_in_sync(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _create_bound_pivot(engine)
    pivot = root.findChild(QObject, "boundPivot")

    try:
        assert pivot is not None
        assert pivot.property("currentIndex") == 0
        assert pivot.property("_prevIndex") == 0
        sync_timer = pivot.findChild(QObject, "pivotIndicatorSyncTimer")
        assert sync_timer is not None
        assert sync_timer.parent() is pivot
        assert sync_timer.property("host") == pivot
        assert sync_timer.property("interval") == root.property(
            "expectedIndicatorSyncInterval"
        )
        assert sync_timer.property("repeat") is True
        assert sync_timer.property("running") is False

        assert root.setProperty("requestedIndex", 2)
        QTest.qWait(STATE_SETTLE_MS)

        assert pivot.property("currentIndex") == 2
        assert pivot.property("_prevIndex") == 2
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_model_shrink_hides_stale_indicator_until_index_is_valid(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _create_bound_pivot(engine)

    try:
        assert root.setProperty("requestedIndex", 2)
        QTest.qWait(STATE_SETTLE_MS)
        pivot, indicator, _animation, _delegates = _pivot_parts(root)
        assert indicator.isVisible()
        assert pivot.property("_prevIndex") == 2

        assert root.setProperty("pivotItems", [{"key": "only", "text": "Only"}])
        QTest.qWait(STATE_SETTLE_MS)
        assert pivot.property("currentIndex") == 2
        assert not indicator.isVisible()
        assert pivot.property("_prevIndex") == -1

        assert root.setProperty("requestedIndex", 0)
        QTest.qWait(STATE_SETTLE_MS)
        pivot, indicator, _animation, delegates = _pivot_parts(root)
        assert indicator.isVisible()
        assert pivot.property("_prevIndex") == 0
        assert len(delegates) == 1
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_same_index_setter_recovers_uninitialized_indicator(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _create_bound_pivot(engine)

    try:
        pivot, indicator, _animation, _delegates = _pivot_parts(root)
        assert pivot.setProperty("_initialized", False)
        assert pivot.setProperty("_prevIndex", -1)
        assert not indicator.isVisible()

        pivot.setCurrentIndex(0)

        assert indicator.isVisible()
        assert pivot.property("_initialized")
        assert pivot.property("_prevIndex") == 0
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_rapid_external_retarget_continues_from_rendered_geometry(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _create_bound_pivot(engine)

    try:
        pivot, _indicator, animation, delegates = _pivot_parts(root)
        assert pivot.setProperty("indicatorAnimationEnabled", True)
        assert root.setProperty("requestedIndex", 2)
        QTest.qWait(80)
        before_retarget = float(animation.property("indicatorX"))
        assert animation.property("running")

        assert root.setProperty("requestedIndex", 1)
        after_retarget = float(animation.property("indicatorX"))
        assert after_retarget == pytest.approx(before_retarget, abs=0.75)
        assert _wait_until(lambda: not animation.property("running"))
        assert animation.property("indicatorX") == pytest.approx(
            _expected_x(pivot, delegates[1]), abs=0.5
        )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
