# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget 左右滑动方向运行时回归测试。"""

from PySide6.QtCore import QElapsedTimer, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QSignalSpy, QTest

from prismqml import register_types


ANIMATION_TIMEOUT_MS = 2_000
COMPONENT_READY_TIMEOUT_MS = 2_000
COMPONENT_READY_POLL_MS = 10


def _build_slide_stack(engine: QQmlApplicationEngine):
    component = QQmlComponent(engine)
    component.setData(
        b"""
import QtQuick
import PrismQML

Item {
    width: 640
    height: 360

    StackedWidget {
        id: stack
        objectName: "slideStack"
        width: parent.width
        height: parent.height
        animationType: Enums.animation.slide
        animationDuration: Enums.duration.fast

        Rectangle { objectName: "page0" }
        Rectangle { objectName: "page1" }
    }
}
""",
        QUrl("inline:stacked-widget-slide-direction"),
    )
    elapsed = QElapsedTimer()
    elapsed.start()
    while component.status() == QQmlComponent.Loading and elapsed.elapsed() < COMPONENT_READY_TIMEOUT_MS:
        QTest.qWait(COMPONENT_READY_POLL_MS)
    assert not component.isError(), [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Ready

    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return component, root


def _switch_and_capture(stack, target_index: int, incoming_page):
    start_positions = []
    finished = QSignalSpy(stack.animationFinished)

    def capture_start_position():
        start_positions.append(float(incoming_page.property("x")))

    stack.animationStarted.connect(capture_start_position)
    try:
        assert stack.setProperty("currentIndex", target_index)
        assert start_positions
        assert finished.wait(ANIMATION_TIMEOUT_MS)
    finally:
        stack.animationStarted.disconnect(capture_start_position)
    return start_positions[0]


def test_slide_direction_follows_index_order(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root = _build_slide_stack(engine)
    stack = root.findChild(QObject, "slideStack")
    page0 = root.findChild(QObject, "page0")
    page1 = root.findChild(QObject, "page1")

    assert stack is not None
    assert page0 is not None
    assert page1 is not None
    stack_width = float(stack.property("width"))

    forward_start_x = _switch_and_capture(stack, 1, page1)
    backward_start_x = _switch_and_capture(stack, 0, page0)

    assert forward_start_x == stack_width
    assert backward_start_x == -stack_width

    root.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    qapp.processEvents()
