# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toast long-message layout regressions. Toast 长消息布局回归。"""

import math
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
from PySide6.QtGui import QFontMetricsF
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
LONG_MESSAGE = (
    "仓库正被另一个 Git 操作占用，本次操作未执行。"
    "请等待其他 Git 操作结束后重试；若确认没有 Git 操作在运行，"
    "请关闭相关 Git 工具，删除仓库中的 .git/index.lock 后再重试。"
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "toast-layout.qml"))
SCENE_SOURCE = f"""
import QtQuick
import PrismQML

Item {{
    readonly property int spacingM: Enums.spacing.m
    readonly property int spacingL: Enums.spacing.l
    readonly property int toastWidth: Enums.controlSize.toastWidth
    readonly property int toastMaxWidth: Enums.controlSize.toastMaxWidth
    readonly property int toastHeight: Enums.controlSize.toastHeight

    width: 1000
    height: 400

    Toast {{
        objectName: "longToast"
        desktopMode: true
        duration: 0
        visible: true
        orient: Qt.Vertical
        severity: "error"
        title: "操作失败"
        message: {LONG_MESSAGE!r}
    }}
}}
""".encode("utf-8")
# Horizontal layout must stay at the default width and stack its text instead of
# widening like a banner. 水平布局必须保持默认宽度, 文本上下堆叠而不是像横幅一样横向变宽。
MID_MESSAGE = "仓库正被另一个 Git 操作占用，本次操作未执行，请稍后重试"
HORIZONTAL_SCENE_SOURCE = f"""
import QtQuick
import PrismQML

Item {{
    readonly property int spacingM: Enums.spacing.m
    readonly property int spacingL: Enums.spacing.l
    readonly property int toastWidth: Enums.controlSize.toastWidth
    readonly property int toastMaxWidth: Enums.controlSize.toastMaxWidth
    readonly property int toastHeight: Enums.controlSize.toastHeight

    width: 1000
    height: 400

    Toast {{
        objectName: "horizontalToast"
        desktopMode: true
        duration: 0
        visible: true
        orient: Qt.Horizontal
        severity: "error"
        title: "操作失败"
        message: {MID_MESSAGE!r}
    }}

    // Progress bar mode + custom action, as used by the in-window updater toast.
    // 进度条模式 + 自定义操作区, 对应窗口内更新 Toast。
    Toast {{
        objectName: "progressToast"
        y: 200
        desktopMode: true
        duration: 0
        visible: true
        orient: Qt.Horizontal
        severity: "info"
        feature: Enums.notification.feature_progress_bar
        progress: 0.4
        title: "下载中"
        message: {MID_MESSAGE!r}
        customContent: Component {{
            Item {{
                implicitWidth: 80
                implicitHeight: 24
            }}
        }}
    }}

    // Long wrapped message in the default horizontal layout, long enough to grow
    // past the minimum toast height on every font. 默认水平布局下的长折行消息,
    // 长到在任何字体下都必须超过 Toast 最小高度。
    Toast {{
        objectName: "longHorizontalToast"
        y: 300
        desktopMode: true
        duration: 0
        visible: true
        orient: Qt.Horizontal
        severity: "error"
        title: "操作失败"
        message: {LONG_MESSAGE!r}
    }}
}}
""".encode("utf-8")


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene(source: bytes = SCENE_SOURCE):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
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


def _visible_text_item(toast: QQuickItem, text: str) -> QQuickItem:
    matches = [
        item
        for item in toast.findChildren(QObject)
        if isinstance(item, QQuickItem)
        and item.property("text") == text
        and item.property("visible")
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _minimum_wrapped_lines(body: QQuickItem, message: str) -> int:
    """Lines this message needs inside the item's own measured text box.

    The exact line count depends on the platform font: a CJK-capable font makes
    this message wider than the text box, while a font without CJK glyphs can fit
    it into one line. Measuring with the item's own font keeps the wrap assertion
    strict wherever the text really overflows, instead of pinning one platform's
    glyph advances.
    该消息在 item 自身文本盒内所需的最少行数。具体行数取决于平台字体: 具备中日韩
    字形的字体让消息宽于文本盒, 而缺少中日韩字形的字体可以把它放进一行。用 item
    自身的字体度量, 使折行断言在文本真正溢出时依旧严格, 而不是钉死某一平台的
    字形宽度。
    """
    metrics = QFontMetricsF(body.property("font"))
    natural_width = metrics.horizontalAdvance(message)
    box_width = body.width()
    if box_width <= 0:
        return 1
    return max(1, math.ceil((natural_width - 1.0) / box_width))


def test_vertical_toast_wraps_downward_with_full_bottom_padding(qapp):
    engine, component, root = _create_scene()
    try:
        toast = root.findChild(QQuickItem, "longToast")
        assert toast is not None
        body = _visible_text_item(toast, LONG_MESSAGE)

        assert len(LONG_MESSAGE) == 100
        assert toast.width() == pytest.approx(root.property("toastWidth"))
        assert toast.width() < root.property("toastMaxWidth")
        assert body.property("lineCount") > 1
        assert toast.height() > root.property("toastHeight")
        assert toast.height() == pytest.approx(toast.property("implicitHeight"))

        body_bottom = body.mapToItem(toast, QPointF(0, body.height())).y()
        expected_bottom_gap = root.property("spacingM") + root.property("spacingL")
        assert toast.height() - body_bottom == pytest.approx(expected_bottom_gap)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_horizontal_toast_keeps_default_width_and_wraps_message(qapp):
    """Horizontal toasts must wrap at the default width instead of stretching.
    水平布局须在默认宽度处折行, 不允许横向拉长。"""
    engine, component, root = _create_scene(HORIZONTAL_SCENE_SOURCE)
    try:
        toast = root.findChild(QQuickItem, "horizontalToast")
        assert toast is not None
        body = _visible_text_item(toast, MID_MESSAGE)

        assert toast.property("orient") == 1  # Qt.Horizontal
        assert toast.width() == pytest.approx(root.property("toastWidth"))
        assert toast.width() < root.property("toastMaxWidth")
        assert body.property("lineCount") >= _minimum_wrapped_lines(body, MID_MESSAGE)
        assert toast.height() == pytest.approx(toast.property("implicitHeight"))

        # The message must stay inside the card instead of overflowing it.
        # 消息必须留在卡片内, 不得溢出卡片。
        body_bottom = body.mapToItem(toast, QPointF(0, body.height())).y()
        card_bottom = toast.height() - root.property("spacingM")
        assert body_bottom <= card_bottom
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_horizontal_toast_grows_for_wrapped_message_and_keeps_bottom_padding(qapp):
    """The horizontal layout must grow with its wrapped text.

    水平布局必须随折行文本一起撑高: 消息底边到 Toast 底边必须保留与垂直布局
    相同的完整底部内边距(卡片内边距 + 阴影外边距), 否则最后一行会被裁掉。
    """
    engine, component, root = _create_scene(HORIZONTAL_SCENE_SOURCE)
    try:
        toast = root.findChild(QQuickItem, "longHorizontalToast")
        assert toast is not None
        body = _visible_text_item(toast, LONG_MESSAGE)

        assert body.property("lineCount") > 1
        assert toast.width() == pytest.approx(root.property("toastWidth"))
        assert toast.height() > root.property("toastHeight")
        assert toast.height() == pytest.approx(toast.property("implicitHeight"))

        body_bottom = body.mapToItem(toast, QPointF(0, body.height())).y()
        expected_bottom_gap = root.property("spacingM") + root.property("spacingL")
        assert toast.height() - body_bottom == pytest.approx(expected_bottom_gap)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_progress_toast_with_custom_content_still_wraps_message(qapp):
    """Custom content must not let a long message stretch the toast.
    自定义内容不得让长消息把 Toast 拉宽。"""
    engine, component, root = _create_scene(HORIZONTAL_SCENE_SOURCE)
    try:
        toast = root.findChild(QQuickItem, "progressToast")
        assert toast is not None
        assert toast.property("hasCustomContent") is True
        body = _visible_text_item(toast, MID_MESSAGE)

        assert toast.width() == pytest.approx(root.property("toastWidth"))
        assert toast.width() < root.property("toastMaxWidth")
        assert body.property("lineCount") >= _minimum_wrapped_lines(body, MID_MESSAGE)

        body_bottom = body.mapToItem(toast, QPointF(0, body.height())).y()
        card_bottom = toast.height() - root.property("spacingM")
        assert body_bottom <= card_bottom
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)
