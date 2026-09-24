# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""RefreshContainer contracts. 下拉刷新契约回归。"""

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


SCENE_URL = QUrl.fromLocalFile(
    str(Path(__file__).resolve().parent / "refresh-container.qml")
)

SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int expectedThreshold: Enums.controlSize.refreshPullThreshold
    property int requestCount: 0

    width: 420
    height: 420
    visible: true

    function finishRefresh() { container.refreshing = false }
    function scrollListDown() { list.contentY = 200 }

    RefreshContainer {
        id: container
        objectName: "refreshContainer"
        x: 20
        y: 20
        width: 360
        height: 300
        onRefreshRequested: root.requestCount++

        Flickable {
            id: list
            objectName: "refreshList"
            anchors.fill: parent
            contentWidth: width
            contentHeight: 900
            boundsBehavior: Flickable.StopAtBounds

            Rectangle {
                width: parent.width
                height: 900
                color: Enums.cardColor
            }
        }
    }
}
"""


def _pump(milliseconds: int = 12) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, SCENE_URL)
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
    window.show()
    _pump(120)
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


def _container(window: QQuickWindow):
    container = window.findChild(QQuickItem, "refreshContainer")
    assert container is not None
    return container


def _pull(window: QQuickWindow, distance: int) -> None:
    """Drag the surface straight down by ``distance`` logical pixels.

    从容器中部竖直向下拖拽指定距离。
    """
    container = _container(window)
    start = container.mapToItem(window.contentItem(), QPointF(180, 80))
    start_point = QPoint(round(start.x()), round(start.y()))
    end_point = QPoint(start_point.x(), start_point.y() + distance)

    QTest.mouseMove(window, start_point)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        start_point,
    )
    QTest.mouseMove(window, QPoint(start_point.x(), start_point.y() + distance // 2), 20)
    QTest.mouseMove(window, end_point, 20)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        end_point,
    )


def test_pull_past_threshold_requests_once_and_holds_until_finished(qapp):
    """A full pull must request one refresh and hold the indicator open.

    完整下拉必须只请求一次刷新，并把指示器保持到宿主结束刷新。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        container = _container(window)
        threshold = window.property("expectedThreshold")
        assert container.property("refreshing") is False

        _pull(window, threshold + 40)
        assert _wait_for(lambda: window.property("requestCount") == 1), (
            f"no refresh requested after a {threshold + 40}px pull"
        )
        assert container.property("refreshing") is True
        assert container.property("progress") == pytest.approx(1, abs=0.01)
        assert container.property("_offset") == pytest.approx(threshold, abs=0.5)

        # The host finishes: the content must settle back 宿主结束后内容归位
        window.finishRefresh()
        assert container.property("refreshing") is False
        assert _wait_for(
            lambda: container.property("_offset") == pytest.approx(0, abs=0.5)
        ), "content did not settle back after the refresh finished"
        # A finished refresh is never re-requested by itself
        # 结束的刷新不会被自己重复触发
        _pump(120)
        assert window.property("requestCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_short_pull_does_not_request_a_refresh(qapp):
    """A pull below the threshold must settle back without requesting.

    未过阈值的下拉必须回弹且不请求刷新。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        container = _container(window)
        threshold = window.property("expectedThreshold")

        _pull(window, max(12, threshold // 3))
        _pump(160)
        assert window.property("requestCount") == 0
        assert container.property("refreshing") is False
        assert container.property("_offset") == pytest.approx(0, abs=0.5)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_pull_is_ignored_when_the_surface_is_not_at_the_top(qapp):
    """Scrolled away from the top, the pull gesture must not engage.

    滚动面离开顶部后，下拉手势不得生效。
    """
    engine, component, window, warnings = _create_scene(qapp)
    try:
        container = _container(window)
        threshold = window.property("expectedThreshold")
        window.scrollListDown()
        assert _wait_for(
            lambda: window.findChild(QObject, "refreshList").property("contentY") > 0
        )

        _pull(window, threshold + 40)
        _pump(160)
        assert window.property("requestCount") == 0
        assert container.property("_offset") == pytest.approx(0, abs=0.5)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
