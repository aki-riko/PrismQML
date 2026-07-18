# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toast long-message layout regressions. Toast 长消息布局回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
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
