# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Toast visible-edge stack spacing regressions. Toast 可见边缘堆叠间距回归。"""

from pathlib import Path
import time

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "toast-stack-spacing.qml")
)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host

    property var firstToast: null
    property var secondToast: null
    readonly property int stackGap: Enums.spacing.m
    readonly property int toastVisualInset: Enums.spacing.m

    function createScreenshotToasts(requestedPosition) {
        firstToast = NotificationManager.toast.info(
            host, "提示", "左上位置", 0, requestedPosition
        )
        secondToast = NotificationManager.toast.info(
            host, "提示", "左上位置", 0, requestedPosition
        )
    }

    function closeToasts() {
        if (firstToast) firstToast.hide()
        if (secondToast) secondToast.hide()
    }

    width: 800
    height: 600
    visible: false
}
""".encode("utf-8")


def _wait_until(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QGuiApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    assert predicate()


def _create_scene() -> tuple[QQmlApplicationEngine, QQmlComponent, QObject]:
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    _wait_until(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root


@pytest.mark.parametrize("position, stacks_upward", [(0, False), (6, True)])
def test_toasts_use_visual_edge_stack_gap(qapp, position, stacks_upward):
    """Screenshot-equivalent Toasts keep one small token between visible edges."""
    engine, component, root = _create_scene()
    try:
        root.createScreenshotToasts(position)
        first = root.property("firstToast")
        second = root.property("secondToast")
        assert isinstance(first, QQuickItem)
        assert isinstance(second, QQuickItem)
        _wait_until(lambda: first.property("visible") and second.property("visible"))
        QTest.qWait(400)

        inset = root.property("toastVisualInset")
        if stacks_upward:
            first_visual_top = first.y() + inset
            second_visual_bottom = second.y() + second.height() - inset
            actual_gap = first_visual_top - second_visual_bottom
        else:
            first_visual_bottom = first.y() + first.height() - inset
            second_visual_top = second.y() + inset
            actual_gap = second_visual_top - first_visual_bottom
        assert actual_gap == pytest.approx(root.property("stackGap"))
    finally:
        root.closeToasts()
        QTest.qWait(300)
        root.deleteLater()
        del component
        engine.deleteLater()
        QGuiApplication.processEvents()
