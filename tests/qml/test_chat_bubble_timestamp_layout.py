# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""ChatBubble timestamp layout contracts. 聊天气泡时间戳排版合同。

时间戳既不能压住正文，也不能把短消息的气泡挤变形。这里把两种模式都钉死：
  - 单行正文且右侧放得下 → 时间戳内联在末行右侧，气泡宽度把两者都装进去；
  - 放不下（多行/超宽） → 正文让出底部一条带，时间戳落进那条带里。
两种情况都必须满足：正文条目与时间戳条目的矩形**不相交**。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]

SCENE_TEMPLATE = """
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    width: 620
    height: 760
    visible: true

    Column {
        Repeater {
            model: %MODEL%

            Fluent.ChatBubble {
                objectName: "bubble" + index
                width: 596
                role: modelData.role
                content: modelData.content
                timestamp: modelData.timestamp
                avatarText: "P"
            }
        }
    }
}
"""

LONG_MULTILINE = (
    "这条够长，气泡宽度受上限约束，正文会折成两行以上，于是时间戳必须让到下面单独一行，"
    "绝不允许压住最后一行文字。"
)

CASES = (
    ("user", "2", "04:26"),
    ("assistant", "在", "04:26"),
    ("user", "这是一条正常长度的消息", "04:26"),
    ("assistant", LONG_MULTILINE, "04:26"),
    ("user", "2", ""),
)


def _pump(milliseconds: int = 60) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _find(root, object_name: str):
    """Recursive lookup: `findChild` misses Repeater delegates. 递归查找（findChild 找不到委托）。"""
    for item in _walk(root):
        if item.objectName() == object_name:
            return item
    return None


def _evaluate(instance, expression_source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, expression_source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return result[0] if isinstance(result, tuple) else result


def _surface(bubble):
    for item in _walk(bubble):
        if "ChatBubbleSurface" in item.metaObject().className():
            return item
    return None


def _rect(item) -> tuple[float, float, float, float]:
    return (
        float(item.property("x")),
        float(item.property("y")),
        float(item.property("width")),
        float(item.property("height")),
    )


def _intersects(first, second) -> bool:
    ax, ay, aw, ah = _rect(first)
    bx, by, bw, bh = _rect(second)
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def _build_scene(engine, cases) -> tuple[object, QQuickWindow]:
    model = "[" + ",".join(
        '{ role: "%s", content: "%s", timestamp: "%s" }'
        % (role, content.replace('"', '\\"'), stamp)
        for role, content, stamp in cases
    ) + "]"
    component = QQmlComponent(engine)
    component.setData(
        SCENE_TEMPLATE.replace("%MODEL%", model).encode("utf-8"),
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "chat-bubble-timestamp-layout.qml")),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create()
    assert isinstance(window, QQuickWindow)
    window.show()
    _pump(400)
    return component, window


def test_timestamp_never_overlaps_content(qapp):
    """五组场景：正文与时间戳的条目矩形一律不得相交。"""
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    component = None
    window = None
    try:
        component, window = _build_scene(engine, CASES)
        for index, (role, content, stamp) in enumerate(CASES):
            bubble = _find(window.contentItem(), "bubble" + str(index))
            assert bubble is not None, index
            surface = _surface(bubble)
            content_item = _find(bubble, "chatBubbleContent")
            stamp_item = _find(bubble, "chatBubbleTimestamp")
            assert surface is not None and content_item is not None and stamp_item is not None

            if not stamp:
                assert stamp_item.property("visible") is False, index
                continue
            assert stamp_item.property("visible") is True, index
            assert not _intersects(content_item, stamp_item), (
                f"第 {index} 组时间戳压住了正文：{content}={_rect(content_item)} "
                f"stamp={_rect(stamp_item)}"
            )
            # 时间戳必须留在气泡里，不许溢出。
            assert _rect(stamp_item)[0] + _rect(stamp_item)[2] <= surface.width() + 0.5, index
        # 绑定环会让 MarkdownView 反复 polish 并刷告警，这里顺带守住。
        assert warnings == [], warnings
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
            QEventLoop().processEvents()
        if component is not None:
            component.deleteLater()
        engine.collectGarbage()


def test_short_message_bubble_is_wide_enough_for_the_timestamp(qapp):
    """单字消息的气泡必须容得下时间戳（此前固定 48px，时间戳被挤到字上）。"""
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = None
    window = None
    try:
        component, window = _build_scene(engine, CASES)
        short_cases = (0, 1)  # "2" / "在"，均为单字 + 时间戳
        for index in short_cases:
            bubble = _find(window.contentItem(), "bubble" + str(index))
            surface = _surface(bubble)
            stamp_item = _find(bubble, "chatBubbleTimestamp")
            pad = float(_evaluate(bubble, "_pad"))
            assert bool(_evaluate(bubble, "_timestampInline")) is True, index
            assert float(_evaluate(bubble, "_footerHeight")) == 0.0, index
            assert surface.width() >= float(stamp_item.property("width")) + pad * 2 - 0.5, index
            assert surface.width() > 48.0, f"单字气泡仍是 48px 地板宽：{surface.width()}"

        # 多行消息走另一条路：底部留出条带，气泡因此比无时间戳时更高，而不是压字。
        multiline = _find(window.contentItem(), "bubble3")
        assert bool(_evaluate(multiline, "_timestampInline")) is False
        assert float(_evaluate(multiline, "_footerHeight")) > 0.0
        stamp_item = _find(multiline, "chatBubbleTimestamp")
        assert float(stamp_item.property("y")) > 0.0
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
            QEventLoop().processEvents()
        if component is not None:
            component.deleteLater()
        engine.collectGarbage()
