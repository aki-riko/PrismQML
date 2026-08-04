# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ImageWidget render lifecycle regressions. ImageWidget 渲染生命周期回归。"""

from __future__ import annotations

from base64 import b64encode
from hashlib import sha256
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "image-widget-layer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 180
    height: 160
    visible: true
    color: Enums.backgroundColor

    ImageWidget {
        id: widget

        objectName: "widget"
        x: 30
        y: 20
        width: 120
        height: 120
        radius: Enums.radius.xlarge
    }
}
"""
IMAGE_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"
viewBox="0 0 64 64"><rect width="64" height="64" fill="#005a9e"/>
<circle cx="32" cy="32" r="20" fill="#ffd43b"/></svg>"""
IMAGE_DATA_URI = "data:image/svg+xml;base64," + b64encode(IMAGE_SVG).decode("ascii")
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(30):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump(20)
    raise AssertionError("ImageWidget frame did not stabilize within 600 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _image_container(widget: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in widget.childItems()
        if any(
            child.metaObject().className() == "QQuickImage"
            for child in item.childItems()
        )
    ]
    assert len(matches) == 1, [
        (item.metaObject().className(), item.objectName())
        for item in widget.childItems()
    ]
    return matches[0]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene():
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    widget = window.findChild(QQuickItem, "widget")
    assert widget is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, widget, warnings, messages, previous_handler


def _dispose_scene(qapp, engine, component, window, previous_handler) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    qInstallMessageHandler(previous_handler)


def _qt_failures(messages) -> list[str]:
    return [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]


def test_image_widget_preserves_empty_ready_empty_frames(qapp):
    """Loading and clearing a real image must preserve stable frames.

    真实图片加载与清空须保持稳定帧。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    engine, component, window, widget, warnings, messages, previous_handler = scene
    try:
        container = _image_container(widget)
        layer_enabled = QQmlProperty(container, "layer.enabled")
        assert layer_enabled.isValid()
        assert widget.property("source") == ""
        assert widget.property("loading") is False
        assert widget.property("error") is False
        assert widget.property("ready") is False
        empty_image = _stable_window_image(window)

        initial_geometry = (
            widget.x(),
            widget.y(),
            widget.width(),
            widget.height(),
            widget.property("radius"),
        )
        widget.setProperty("source", IMAGE_DATA_URI)
        assert _wait_for(lambda: widget.property("ready"))
        assert widget.property("loading") is False
        assert widget.property("error") is False
        assert widget.property("sourceWidth") == 64
        assert widget.property("sourceHeight") == 64
        ready_image = _stable_window_image(window)
        assert ready_image != empty_image
        assert initial_geometry == (
            widget.x(),
            widget.y(),
            widget.width(),
            widget.height(),
            widget.property("radius"),
        )

        widget.setProperty("source", "")
        assert _wait_for(lambda: not widget.property("ready"))
        restored_image = _stable_window_image(window)
        assert restored_image == empty_image
        assert warnings == []
        assert _qt_failures(messages) == []
        assert _new_visible_windows(windows_before, window) == []

        print(
            "IMAGE_WIDGET_FRAMES",
            f"empty={_image_hash(empty_image)}",
            f"ready={_image_hash(ready_image)}",
            f"restored={_image_hash(restored_image)}",
        )
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)
        assert _new_visible_windows(windows_before) == []
