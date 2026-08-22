# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StackedWidget 全动画模式运行时语义回归测试。"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from PySide6.QtCore import QElapsedTimer, QObject, QSignalBlocker, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QSignalSpy, QTest

from prismqml import register_types


ANIMATION_DURATION_MS = 160
ANIMATION_TIMEOUT_MS = 2_000
COMPONENT_READY_TIMEOUT_MS = 2_000
POLL_INTERVAL_MS = 5
MODE_NAMES = ("opacity", "popup", "popdown", "slide", "card", "zoom")


def _wait_until(predicate: Callable[[], bool], timeout_ms: int) -> bool:
    elapsed = QElapsedTimer()
    elapsed.start()
    while not predicate() and elapsed.elapsed() < timeout_ms:
        QTest.qWait(POLL_INTERVAL_MS)
    return predicate()


def _evaluate(root: QObject, expression: str):
    qml_expression = QQmlExpression(QQmlEngine.contextForObject(root), root, expression)
    value = qml_expression.evaluate()
    assert not qml_expression.hasError(), qml_expression.error().toString()
    return value[0] if isinstance(value, tuple) else value


def _build_stack(engine: QQmlApplicationEngine, mode_name: str):
    component = QQmlComponent(engine)
    source = f"""
import QtQuick
import PrismQML

Item {{
    width: 320
    height: 200
    readonly property int popupMode: Enums.animation.popup
    readonly property int popdownMode: Enums.animation.popdown

    StackedWidget {{
        id: stack
        objectName: "animationStack"
        anchors.fill: parent
        animationType: Enums.animation.{mode_name}
        animationDuration: {ANIMATION_DURATION_MS}

        Item {{ objectName: "page0" }}
        Item {{ objectName: "page1" }}
    }}
}}
""".encode("utf-8")
    component.setData(source, QUrl(f"inline:stacked-widget-{mode_name}-animations"))
    assert _wait_until(
        lambda: component.status() != QQmlComponent.Status.Loading,
        COMPONENT_READY_TIMEOUT_MS,
    )
    assert not component.isError(), [error.toString() for error in component.errors()]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    stack = root.findChild(QObject, "animationStack")
    page0 = root.findChild(QObject, "page0")
    page1 = root.findChild(QObject, "page1")
    assert stack is not None and page0 is not None and page1 is not None
    return component, root, stack, page0, page1


def _number(item: QObject, name: str) -> float:
    return float(item.property(name))


def _assert_close(actual: float, expected: float) -> None:
    assert actual == pytest.approx(expected, abs=0.001)


def _assert_resting_state(current: QObject, previous: QObject) -> None:
    assert bool(current.property("visible"))
    assert not bool(previous.property("visible"))
    for name, expected in (("x", 0), ("y", 0), ("scale", 1), ("opacity", 1)):
        _assert_close(_number(current, name), expected)
        _assert_close(_number(previous, name), expected)


def _assert_current_resting_state(current: QObject, previous: QObject) -> None:
    assert bool(current.property("visible"))
    assert not bool(previous.property("visible"))
    for name, expected in (("x", 0), ("y", 0), ("scale", 1), ("opacity", 1)):
        _assert_close(_number(current, name), expected)


def _assert_enter_resting_state(current: QObject, previous: QObject) -> None:
    assert bool(current.property("visible"))
    assert not bool(previous.property("visible"))
    for name, expected in (("x", 0), ("y", 0), ("scale", 1), ("opacity", 1)):
        _assert_close(_number(current, name), expected)
    _assert_close(_number(previous, "opacity"), 0)


def _assert_transition_start(
    mode_name: str, stack: QObject, old_page: QObject, new_page: QObject, is_back: bool
) -> None:
    width = _number(stack, "width")
    offset = _number(stack, "popUpOffset")
    assert bool(new_page.property("visible")) or mode_name == "zoom"
    if mode_name == "opacity":
        assert bool(old_page.property("visible"))
        _assert_close(_number(new_page, "opacity"), 0)
    elif mode_name in {"popup", "popdown"}:
        assert not bool(old_page.property("visible"))
        _assert_close(_number(new_page, "y"), offset if mode_name == "popup" else -offset)
        _assert_close(_number(new_page, "opacity"), 0)
    elif mode_name == "slide":
        assert bool(old_page.property("visible"))
        _assert_close(_number(new_page, "x"), -width if is_back else width)
    elif mode_name == "card":
        assert bool(old_page.property("visible"))
        _assert_close(_number(new_page, "x"), 0 if is_back else width)
        expected_scale = _number(stack, "cardScale") if is_back else 1
        expected_opacity = _number(stack, "cardOpacity") if is_back else 1
        _assert_close(_number(new_page, "scale"), expected_scale)
        _assert_close(_number(new_page, "opacity"), expected_opacity)
    else:
        assert bool(old_page.property("visible"))
        assert not bool(new_page.property("visible"))
        _assert_close(_number(old_page, "scale"), 1)


def _switch_and_verify(
    stack: QObject,
    old_page: QObject,
    new_page: QObject,
    mode_name: str,
    target_index: int,
    expected_finished: int,
) -> None:
    finished = QSignalSpy(stack.animationFinished)
    assert stack.setProperty("currentIndex", target_index)
    _assert_transition_start(mode_name, stack, old_page, new_page, target_index == 0)
    assert _wait_until(lambda: finished.count() == expected_finished, ANIMATION_TIMEOUT_MS)
    _assert_resting_state(new_page, old_page)


def _dispose(engine: QQmlApplicationEngine, component: QQmlComponent, root: QObject) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    QTest.qWait(POLL_INTERVAL_MS)


@pytest.mark.parametrize("mode_name", MODE_NAMES)
def test_all_modes_preserve_forward_and_backward_states(qapp, mode_name):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root, stack, page0, page1 = _build_stack(engine, mode_name)
    try:
        _switch_and_verify(stack, page0, page1, mode_name, 1, 1)
        _switch_and_verify(stack, page1, page0, mode_name, 0, 1)
    finally:
        _dispose(engine, component, root)


def _assert_enter_start(mode_name: str, stack: QObject, page: QObject) -> None:
    offset = _number(stack, "popUpOffset")
    if mode_name == "opacity":
        _assert_close(_number(page, "opacity"), 0)
    elif mode_name in {"popup", "popdown"}:
        _assert_close(_number(page, "y"), offset if mode_name == "popup" else -offset)
        _assert_close(_number(page, "opacity"), 0)
    elif mode_name in {"slide", "card"}:
        _assert_close(_number(page, "x"), _number(stack, "width"))
    else:
        _assert_close(_number(page, "scale"), 0)


@pytest.mark.parametrize("mode_name", MODE_NAMES)
def test_all_modes_preserve_enter_only_states(qapp, mode_name):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root, stack, page0, page1 = _build_stack(engine, mode_name)
    try:
        finished = QSignalSpy(stack.animationFinished)
        blocker = QSignalBlocker(stack)
        assert stack.setProperty("currentIndex", 1)
        del blocker
        assert bool(_evaluate(root, "stack._completePythonLazySwitch(1)"))
        assert not bool(page0.property("visible"))
        assert bool(page1.property("visible"))
        _assert_enter_start(mode_name, stack, page1)
        assert _wait_until(lambda: finished.count() == 1, ANIMATION_TIMEOUT_MS)
        _assert_enter_resting_state(page1, page0)
    finally:
        _dispose(engine, component, root)


def test_switching_mode_interrupts_old_backend_without_extra_completion(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root, stack, page0, page1 = _build_stack(engine, "slide")
    try:
        finished = QSignalSpy(stack.animationFinished)
        assert stack.setProperty("currentIndex", 1)
        QTest.qWait(ANIMATION_DURATION_MS // 4)
        assert finished.count() == 0
        assert stack.setProperty("animationType", root.property("popupMode"))
        assert stack.setProperty("currentIndex", 0)
        _assert_transition_start("popup", stack, page1, page0, True)
        assert _wait_until(lambda: finished.count() == 1, ANIMATION_TIMEOUT_MS)
        _assert_current_resting_state(page0, page1)
    finally:
        _dispose(engine, component, root)


def test_switching_between_pop_modes_reconfigures_shared_backend(qapp):
    """同一 Loader source 在 PopUp/PopDown 间切换时仍更新方向与 easing。"""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, root, stack, page0, page1 = _build_stack(engine, "popup")
    try:
        finished = QSignalSpy(stack.animationFinished)
        assert stack.setProperty("currentIndex", 1)
        _assert_transition_start("popup", stack, page0, page1, False)
        assert _wait_until(lambda: finished.count() == 1, ANIMATION_TIMEOUT_MS)

        assert stack.setProperty("animationType", root.property("popdownMode"))
        finished = QSignalSpy(stack.animationFinished)
        assert stack.setProperty("currentIndex", 0)
        _assert_transition_start("popdown", stack, page1, page0, True)
        assert _wait_until(lambda: finished.count() == 1, ANIMATION_TIMEOUT_MS)
        _assert_resting_state(page0, page1)
    finally:
        _dispose(engine, component, root)
