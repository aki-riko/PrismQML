# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""InfoBar horizontal text layout regressions. InfoBar 水平文本布局回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
TITLE = "剑网三工具"
# Title + long body, the shape that used to size the body from the bar's maximum
# width and let the wrapped line run over the close button.
# 标题 + 长正文: 旧实现用信息条最大宽度反推正文宽度, 折行会压到关闭按钮上。
#
# The message must be long enough that its natural advance exceeds the bar's
# maximum width on every platform font, otherwise the bar legitimately shrinks to
# its content instead of hitting the cap and the width assertion below would pin
# one platform's glyph advances (Windows CJK glyphs measured 14.0 px/char, a
# fontless Linux runner measured 8.5 px/char; the fixed chrome is 94 px, so the
# cap needs 51 and 83 characters respectively).
# 正文必须长到在任何平台字体下自然宽度都超过信息条上限: 否则信息条会合法地按内容
# 收缩而不是顶到上限, 下面的宽度断言就等于钉死某一平台的字形宽度 (实测 Windows 中日韩
# 字形 14.0 px/字, 无中日韩字形的 Linux runner 8.5 px/字; 固定装饰 94 px, 顶到上限
# 分别只需 51 与 83 字)。
LONG_MESSAGE = (
    "源角色和目标角色都不能在线。新角色必须至少进入过一次游戏并退回角色选择界面，"
    "否则本地配置尚未生成，无法同步。请先退出当前角色并确认本地配置文件已经写入，"
    "再重新选择需要同步的角色。若仍然失败，请关闭游戏后重新打开同步面板再试一次。"
    "同步开始后请不要关闭工具窗口，完成后会自动提示结果。如遇网络异常，请稍后重试。"
)
SHORT_MESSAGE = "目标角色尚未生成本地配置，请先进入游戏并退回角色选择界面"
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "infobar-layout.qml"))
SCENE_SOURCE = f"""
import QtQuick
import PrismQML

Item {{
    // InfoBarContent.maxWidth contract: long content never widens the bar past it.
    // InfoBarContent.maxWidth 契约: 任何长内容都不得把信息条撑过该宽度。
    readonly property int barMaxWidth: 800
    readonly property int barMinWidth: Enums.controlSize.toastWidth
    readonly property int textRightMargin: Enums.infoBarMetrics.textRightMargin

    width: 1100
    height: 800

    InfoBarCore {{
        objectName: "titledLongBar"
        desktopMode: true
        duration: 0
        visible: true
        severity: "warning"
        title: {TITLE!r}
        message: {LONG_MESSAGE!r}
    }}

    InfoBarCore {{
        objectName: "titledShortBar"
        y: 200
        desktopMode: true
        duration: 0
        visible: true
        severity: "warning"
        title: {TITLE!r}
        message: {SHORT_MESSAGE!r}
    }}

    InfoBarCore {{
        objectName: "untitledLongBar"
        y: 400
        desktopMode: true
        duration: 0
        visible: true
        severity: "warning"
        message: {LONG_MESSAGE!r}
    }}
}}
""".encode("utf-8")


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(1)
    return engine, component, root


def _dispose_scene(engine, component, root) -> None:
    root.deleteLater()
    del component
    engine.deleteLater()
    _pump(1)


def _visible_text_item(bar: QQuickItem, text: str) -> QQuickItem:
    matches = [
        item
        for item in bar.findChildren(QObject)
        if isinstance(item, QQuickItem)
        and item.property("text") == text
        and item.isVisible()
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _close_button(bar: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in bar.findChildren(QObject)
        if isinstance(item, QQuickItem)
        and "CloseButton" in item.metaObject().className()
        and item.property("visible")
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _right_edge(bar: QQuickItem, item: QQuickItem) -> float:
    return item.mapToItem(bar, QPointF(0, 0)).x() + item.width()


def _left_edge(bar: QQuickItem, item: QQuickItem) -> float:
    return item.mapToItem(bar, QPointF(0, 0)).x()


def test_titled_infobar_wraps_message_clear_of_close_button(qapp):
    """A titled long message must wrap inside the box left of the close button.

    带标题的长正文必须在关闭按钮左侧的预留区域内折行: 旧实现把正文宽度按信息条
    最大宽度反推, 折行后的文本右边缘越过了关闭按钮左边缘并盖住关闭图标。
    """
    engine, component, root = _create_scene()
    try:
        bar = root.findChild(QQuickItem, "titledLongBar")
        assert bar is not None
        body = _visible_text_item(bar, LONG_MESSAGE)
        closer = _close_button(bar)
        title = _visible_text_item(bar, TITLE)

        body_right = _right_edge(bar, body)
        close_left = _left_edge(bar, closer)

        assert bar.width() == pytest.approx(root.property("barMaxWidth"))
        assert len(LONG_MESSAGE) >= 150
        assert body.property("lineCount") > 1
        assert _right_edge(bar, title) <= close_left
        # The regression: the wrapped line must stay left of the close button and
        # inside the card instead of covering the close icon.
        # 回归点: 折行右边缘必须留在关闭按钮左侧与卡片内部, 不得盖住关闭图标。
        assert body_right <= close_left
        assert body_right <= bar.width()
        assert body_right <= bar.width() - root.property("textRightMargin")
    finally:
        _dispose_scene(engine, component, root)


def test_titled_infobar_keeps_short_message_compact(qapp):
    """A short message still shrinks the bar instead of filling the maximum width.

    短正文仍按内容收缩信息条, 不因为正文宽度改为按真实可用宽度计算而被动撑满。
    """
    engine, component, root = _create_scene()
    try:
        bar = root.findChild(QQuickItem, "titledShortBar")
        assert bar is not None
        body = _visible_text_item(bar, SHORT_MESSAGE)
        closer = _close_button(bar)

        assert bar.width() < root.property("barMaxWidth")
        assert bar.width() >= root.property("barMinWidth")
        assert body.property("lineCount") == 1
        assert _right_edge(bar, body) <= _left_edge(bar, closer)
    finally:
        _dispose_scene(engine, component, root)


def test_untitled_infobar_wraps_inside_the_card(qapp):
    """Without a title the message keeps the full box inside the card.

    无标题时正文占满卡片内留给文字的整块区域, 且不越出卡片边界。
    """
    engine, component, root = _create_scene()
    try:
        bar = root.findChild(QQuickItem, "untitledLongBar")
        assert bar is not None
        body = _visible_text_item(bar, LONG_MESSAGE)
        closer = _close_button(bar)

        assert bar.width() == pytest.approx(root.property("barMaxWidth"))
        assert len(LONG_MESSAGE) >= 150
        assert body.property("lineCount") > 1
        assert _right_edge(bar, body) <= _left_edge(bar, closer)
        assert _right_edge(bar, body) <= bar.width() - root.property("textRightMargin")
    finally:
        _dispose_scene(engine, component, root)
