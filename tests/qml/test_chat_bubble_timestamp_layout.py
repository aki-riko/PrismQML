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

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
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
    // 不显示：本用例只验几何，不需要真渲染；显示窗口会污染同进程后续用例的顶层窗口集合
    // （0.5.0.51 的 release 门禁就红在 test_navigation_view_tooltip 的那条窗口集合断言）。
    visible: false

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

LONG_TEXT = (
    "这条够长，气泡宽度受上限约束，正文会折成两行以上，于是时间戳必须让到下面单独一行，"
    "绝不允许压住最后一行文字。"
)

CASES = (
    ("user", "2", "04:26"),
    ("assistant", "在", "04:26"),
    ("user", "这是一条正常长度的消息", "04:26"),
    # 🔴 判定「多行」只能用显式换行，不能用长文本：长文本量出来的宽度受字体回退影响
    #    （Linux CI 上没有中文字体时明显更窄），同一段文字在 Windows 上算多行、在 Linux 上
    #    可能算单行——0.5.0.50 的 release 门禁就红在这里。
    ("assistant", "第一行\\n第二行", "04:26"),
    ("assistant", LONG_TEXT, "04:26"),
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
    _pump(400)
    return component, window


def _dispose(engine, component, window) -> None:
    """与 test_chat_bubble_shadow_lifecycle 同一套清理。"""
    if window is not None:
        window.close()
        window.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    # 再多跑一会儿事件循环：窗口销毁后 Qt 的顶层窗口表不是立刻剪掉的，太快返回会让**下一个**
    # 用例快照到一个「已删除的僵尸窗口」，把窗口集合断言弄红（CI 实测，0.5.0.51/0.53 两次）。
    _pump(60)


def test_timestamp_lives_outside_the_bubble(qapp):
    """时间戳必须挂在气泡**外侧**，且与正文、气泡都不相交。

    曾经它锚在气泡内右下角、正文又铺满整宽，于是每条带时间戳的消息最后一行都被盖住
    （实测单字消息里 "2" 与 "04:26" 直接叠在一起）。现在外面就没有争位的可能。
    """
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

            # 与正文、与气泡本体都不得相交。
            assert not _intersects(content_item, stamp_item), (
                f"第 {index} 组时间戳压住了正文：{_rect(content_item)} {_rect(stamp_item)}"
            )
            assert not _intersects(surface, stamp_item), (
                f"第 {index} 组时间戳压在气泡上：气泡 {_rect(surface)} 时间戳 {_rect(stamp_item)}"
            )

            # 站位：自己消息在气泡左侧，对方消息在气泡右侧。
            stamp_x, _, stamp_w, _ = _rect(stamp_item)
            surface_x, _, surface_w, _ = _rect(surface)
            if role == "user":
                assert stamp_x + stamp_w <= surface_x + 0.5, (index, _rect(stamp_item), _rect(surface))
            else:
                assert stamp_x >= surface_x + surface_w - 0.5, (index, _rect(stamp_item), _rect(surface))
            # 必须留在这一行的宽度里，不许溢出。
            assert stamp_x >= -0.5 and stamp_x + stamp_w <= bubble.width() + 0.5, index
        assert warnings == [], warnings
    finally:
        _dispose(engine, component, window)


def test_short_message_bubble_keeps_its_own_width(qapp):
    """单字消息的气泡仍按内容定宽（不再被时间戳撑宽），并把时间戳条带让出来。"""
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = None
    window = None
    try:
        component, window = _build_scene(engine, CASES)
        for index in (0, 1):  # "2" / "在"，单字 + 时间戳
            bubble = _find(window.contentItem(), "bubble" + str(index))
            surface = _surface(bubble)
            stamp_item = _find(bubble, "chatBubbleTimestamp")
            width = float(_evaluate(bubble, "_bubbleWidth"))
            assert float(surface.width()) == pytest.approx(width), index
            # 时间戳在气泡外面，所以气泡不再需要为它加宽。
            assert float(surface.width()) < 80.0, (index, surface.width())
            assert float(stamp_item.property("width")) > 0.0, index

        # 气泡宽度上限必须给时间戳条带留出空间，否则贴边的气泡会把时间戳挤出可视区。
        band = float(_evaluate(_find(window.contentItem(), "bubble0"), "_timestampBand"))
        assert band > 0.0
        cap = float(_evaluate(_find(window.contentItem(), "bubble4"), "_capWidth"))
        avail = float(_evaluate(_find(window.contentItem(), "bubble4"), "_availWidth"))
        assert cap <= avail + 0.5
        assert avail <= 596.0 - band + 0.5
    finally:
        _dispose(engine, component, window)
