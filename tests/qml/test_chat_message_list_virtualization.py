# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ChatMessageList long-session virtualization regressions. 聊天长会话虚拟化回归测试。"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine, QQmlExpression

from prismqml import register_types


MESSAGE_COUNT = 1_000
MAX_ACTIVE_MESSAGES = 80
MAX_VISUAL_OBJECTS = 4_000

WINDOW_SOURCE = b"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    visible: false
    width: 900
    height: 640

    ChatMessageList {
        id: messages

        objectName: "messages"
        anchors.fill: parent
    }
}
"""

DESTROY_PENDING_SOURCE = b"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    visible: false
    property bool listActive: true

    Loader {
        id: listLoader

        active: root.listActive
        sourceComponent: ChatMessageList { }
    }

    function appendAndDestroy() {
        listLoader.item.appendMessage("user", "lifecycle regression", "")
        listActive = false
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create(engine: QQmlApplicationEngine, source: bytes = WINDOW_SOURCE):
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:chat-message-list-virtualization.qml"))
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
    return component, window


def _evaluate(instance: QObject, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        if is_undefined:
            return None
    return result


def _wait_until(predicate, timeout_ms: int = 10_000) -> None:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return
        _pump(20)
        elapsed += 20
    pytest.fail(f"condition not met within {timeout_ms} ms")


def _walk_visual_tree(root: QQuickItem):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(item.childItems())


def _message_slots(message_list: QQuickItem) -> list[QQuickItem]:
    content = message_list.findChild(QQuickItem, "chatMessageContent")
    assert content is not None
    return sorted(
        (
            item
            for item in content.childItems()
            if item.metaObject().indexOfProperty("_measuredHeight") >= 0
        ),
        key=lambda item: item.property("index"),
    )


def _is_slot_measured(slot: QQuickItem) -> bool:
    return (
        bool(slot.property("active"))
        and bool(slot.childItems())
        and slot.property("_measuredKey") == slot.property("_measurementKey")
    )


def _has_measured_viewport_slot(
    message_list: QQuickItem, viewport: QQuickItem
) -> bool:
    viewport_top = viewport.property("contentY")
    viewport_bottom = viewport_top + viewport.property("height")
    return any(
        _is_slot_measured(slot)
        and slot.y() + slot.height() >= viewport_top
        and slot.y() <= viewport_bottom
        for slot in _message_slots(message_list)
    )


def _populate_mixed_session(message_list: QQuickItem) -> None:
    long_answer = "\n\n".join(
        f"### 分析段落 {index}\n这是用于验证 Markdown 变高布局的代表性长度文本。"
        for index in range(12)
    )
    script = """(function() {
        for (var i = 0; i < %d; i++) {
            if (i %% 2 === 0) {
                appendMessage("user", "短问题 " + i, "")
            } else {
                appendMessage("assistant", %s + "\\n\\n序号: " + i, "")
            }
        }
        return true
    })()""" % (MESSAGE_COUNT, repr(long_answer))
    assert _evaluate(message_list, script) is True


def test_long_mixed_session_keeps_only_viewport_bubbles_alive(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = window = None
    try:
        component, window = _create(engine)
        message_list = window.findChild(QQuickItem, "messages")
        assert message_list is not None

        _populate_mixed_session(message_list)
        _wait_until(
            lambda: message_list.property("messageCount") == MESSAGE_COUNT
            and len(_message_slots(message_list)) == MESSAGE_COUNT
            and _is_slot_measured(_message_slots(message_list)[-1])
        )

        slots = _message_slots(message_list)
        active_slots = [slot for slot in slots if slot.property("active")]
        loaded_slots = [slot for slot in slots if slot.childItems()]
        visual_objects = sum(1 for _ in _walk_visual_tree(message_list))
        assert 0 < len(loaded_slots) <= len(active_slots) <= MAX_ACTIVE_MESSAGES, (
            len(active_slots),
            len(loaded_slots),
            visual_objects,
        )
        assert visual_objects < MAX_VISUAL_OBJECTS
        assert [slot.property("index") for slot in active_slots] == list(
            range(
                message_list.property("_firstLoadIndex"),
                message_list.property("_lastLoadIndex") + 1,
            )
        )

        viewport = message_list.findChild(QQuickItem, "chatMessageViewport")
        assert viewport is not None
        bottom_gap = viewport.property("contentHeight") - (
            viewport.property("contentY") + viewport.property("height")
        )
        assert abs(bottom_gap) <= 1
        assert slots[-1].y() + slots[-1].height() == pytest.approx(
            viewport.property("contentHeight"), abs=1
        )

        midpoint = viewport.property("contentHeight") / 2
        _evaluate(message_list, f"_setContentY({midpoint}, false)")
        _wait_until(lambda: _has_measured_viewport_slot(message_list, viewport))
        assert 0 < viewport.property("contentY") < (
            viewport.property("contentHeight") - viewport.property("height")
        )
        assert len(
            [slot for slot in _message_slots(message_list) if slot.property("active")]
        ) <= MAX_ACTIVE_MESSAGES
        assert message_list.property("_firstLoadIndex") > 0
        assert message_list.property("_lastLoadIndex") < MESSAGE_COUNT - 1

        _evaluate(message_list, "scrollToEnd()")
        _wait_until(lambda: _is_slot_measured(_message_slots(message_list)[-1]))
        bottom_gap = viewport.property("contentHeight") - (
            viewport.property("contentY") + viewport.property("height")
        )
        assert abs(bottom_gap) <= 1
    finally:
        if window is not None:
            window.deleteLater()
        engine.deleteLater()
        del component
        _pump(1)


def test_streaming_growth_follows_bottom_but_preserves_scrolled_position(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = window = None
    try:
        component, window = _create(engine)
        message_list = window.findChild(QQuickItem, "messages")
        assert message_list is not None
        _populate_mixed_session(message_list)
        _wait_until(lambda: _is_slot_measured(_message_slots(message_list)[-1]))

        _evaluate(message_list, 'appendToLast("\\n\\n流式追加后的尾部内容。")')
        _wait_until(
            lambda: _is_slot_measured(_message_slots(message_list)[-1])
            and message_list.property("_lastLayoutStartIndex")
            == MESSAGE_COUNT - 1
        )
        viewport = message_list.findChild(QQuickItem, "chatMessageViewport")
        bottom_gap = viewport.property("contentHeight") - (
            viewport.property("contentY") + viewport.property("height")
        )
        assert abs(bottom_gap) <= 1

        _evaluate(message_list, "_setContentY(0, false)")
        _pump(20)
        assert viewport.property("contentY") == pytest.approx(0, abs=1)
        _evaluate(message_list, 'appendToLast("\\n不会强制跳回底部。")')
        _pump(100)
        assert viewport.property("contentY") == pytest.approx(0, abs=1)
    finally:
        if window is not None:
            window.deleteLater()
        engine.deleteLater()
        del component
        _pump(1)


def test_clear_resets_virtual_content_extent(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = window = None
    try:
        component, window = _create(engine)
        message_list = window.findChild(QQuickItem, "messages")
        assert message_list is not None
        _populate_mixed_session(message_list)
        _wait_until(lambda: _is_slot_measured(_message_slots(message_list)[-1]))

        viewport = message_list.findChild(QQuickItem, "chatMessageViewport")
        content = message_list.findChild(QQuickItem, "chatMessageContent")
        assert viewport is not None
        assert content is not None
        assert viewport.property("contentHeight") > viewport.property("height")

        _evaluate(message_list, "clear()")
        _wait_until(
            lambda: message_list.property("messageCount") == 0
            and not _message_slots(message_list)
        )

        assert viewport.property("contentY") == pytest.approx(0, abs=1)
        assert viewport.property("contentHeight") == pytest.approx(0, abs=1)
        assert content.property("height") == pytest.approx(0, abs=1)
    finally:
        if window is not None:
            window.deleteLater()
        engine.deleteLater()
        del component
        _pump(1)


def test_destroying_list_cancels_pending_layout_callbacks(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = window = None
    try:
        component, window = _create(engine, DESTROY_PENDING_SOURCE)

        _evaluate(window, "appendAndDestroy()")
        _pump(20)

        assert warnings == []
    finally:
        if window is not None:
            window.deleteLater()
        engine.deleteLater()
        del component
        _pump(1)
