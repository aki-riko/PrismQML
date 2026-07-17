# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker circle async-width regression. 圆形颜色选择器异步宽度回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from prismqml.python.core.incubation import install_incubation_controller


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-circle-async-width.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property bool asyncReady: asyncLoader.item !== null
    readonly property real asyncWidth: asyncLoader.item
        ? asyncLoader.item.implicitWidth
        : -1
    readonly property real syncWidth: syncPicker.implicitWidth

    width: 400
    height: 100

    ColorPicker {
        id: syncPicker
        type: Enums.colorPicker.type_circle
    }

    Loader {
        id: asyncLoader
        asynchronous: true
        sourceComponent: ColorPicker {
            type: Enums.colorPicker.type_circle
        }
    }
}
"""


def _pump(milliseconds: int = 5) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def test_public_circle_async_loader_currently_collapses_width(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    controller = install_incubation_controller(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        for _ in range(40):
            controller.incubateFor(5)
            _pump()
            if root.property("asyncReady"):
                break
        assert root.property("asyncReady")
        assert root.property("syncWidth") == pytest.approx(276)
        assert root.property("asyncWidth") == pytest.approx(0)
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
