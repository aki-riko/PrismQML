# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Navigation icon layer lifecycle regressions. 导航图标层生命周期回归。"""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from threading import Event

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QSize,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
    QQmlProperty,
)
from PySide6.QtQuick import QQuickImageProvider, QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-icon-layer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 560
    height: 220
    visible: true
    color: Enums.backgroundColor

    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.xl

        Column {
            NavigationViewItem {
                objectName: "viewSvg"
                width: 220
                text: "View SVG"
                icon: Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/Settings.svg")
            }

            NavigationViewItem {
                objectName: "viewAvatar"
                width: 220
                text: "View Avatar"
                icon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
            }
        }

        Row {
            NavigationBarItem {
                objectName: "barSvg"
                text: "Bar SVG"
                icon: Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/Settings.svg")
            }

            NavigationBarItem {
                objectName: "barAvatar"
                text: "Bar Avatar"
                icon: Qt.resolvedUrl("../../examples/resources/image/avatar/avatar.png")
            }
        }
    }
}
"""
ITEM_SOURCES = (
    ("viewSvg", "image://navprobe/view.svg"),
    ("viewAvatar", "image://navprobe/view.png"),
    ("barSvg", "image://navprobe/bar.svg"),
    ("barAvatar", "image://navprobe/bar.png"),
)
ERROR_SOURCES = (
    "image://navprobe/error-view.svg",
    "image://navprobe/error-view.png",
    "image://navprobe/error-bar.svg",
    "image://navprobe/error-bar.png",
)
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


class _BlockingNavigationIconProvider(QQuickImageProvider):
    """Hold navigation image requests at Loading. 导航图片请求保持在加载态。"""

    def __init__(self):
        super().__init__(
            QQuickImageProvider.ImageType.Image,
            QQuickImageProvider.Flag.ForceAsynchronousImageLoading,
        )
        self.request_started = Event()
        self.release_requests = Event()

    def requestImage(self, provider_id: str, size: QSize, requested_size: QSize):
        """Return deterministic pixels after release. 放行后返回确定性像素。"""
        del requested_size
        self.request_started.set()
        if not self.release_requests.wait(timeout=2):
            return QImage()
        if provider_id.startswith("error-"):
            return QImage()
        image = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0xFF276FBF if provider_id.endswith(".svg") else 0xFFD08030)
        size.setWidth(image.width())
        size.setHeight(image.height())
        return image


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
        _pump()
    raise AssertionError("Navigation icon frame did not stabilize within 600 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    descendants = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        descendants.append(item)
        pending.extend(item.childItems())
    return descendants


def _image_item(item: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in _visual_descendants(item)
        if child.metaObject().indexOfProperty("fillMode") >= 0
    ]
    assert len(matches) == 1, [
        (child.metaObject().className(), child.objectName())
        for child in _visual_descendants(item)
    ]
    return matches[0]


def _image_count(item: QQuickItem) -> int:
    return sum(
        child.metaObject().indexOfProperty("fillMode") >= 0
        for child in _visual_descendants(item)
    )


def _evaluate(instance: QQuickItem, source: str):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(instance), instance, source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def _all_status(images: tuple[QQuickItem, ...], status: str) -> bool:
    return all(_evaluate(image, f"status === Image.{status}") for image in images)


def _layer_states(images: tuple[QQuickItem, ...]) -> tuple[bool, ...]:
    properties = [QQmlProperty(image, "layer.enabled") for image in images]
    assert all(layer.isValid() for layer in properties)
    return tuple(bool(layer.read()) for layer in properties)


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _qt_failures(messages) -> list[str]:
    return [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]


def _create_scene():
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    provider = _BlockingNavigationIconProvider()
    engine.addImageProvider("navprobe", provider)
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
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
    items = tuple(
        window.findChild(QQuickItem, object_name) for object_name, _source in ITEM_SOURCES
    )
    assert all(item is not None for item in items)
    assert _wait_for(window.isExposed)
    assert _wait_for(
        lambda: all(_image_count(item) == 1 for item in items)
    ), "; ".join(
        f"{object_name}={_image_count(item)}:{item.property('icon')}"
        for item, (object_name, _source) in zip(items, ITEM_SOURCES, strict=True)
    ) + f"; warnings={warnings}; messages={messages}"
    images = tuple(_image_item(item) for item in items)
    assert _wait_for(lambda: _all_status(images, "Ready"))
    return (
        engine,
        component,
        window,
        items,
        provider,
        warnings,
        messages,
        previous_handler,
    )


def _dispose_scene(qapp, engine, component, window, provider, previous_handler):
    provider.release_requests.set()
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    qInstallMessageHandler(previous_handler)


def test_navigation_icon_layers_preserve_first_ready_frame(qapp):
    """Four navigation renderers must preserve their first Ready frame.

    四条导航渲染路径必须保持首个就绪帧。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        items,
        provider,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        assert _wait_for(lambda: all(_image_count(item) == 1 for item in items))
        images = tuple(_image_item(item) for item in items)
        assert _all_status(images, "Ready")
        assert all(image.setProperty("asynchronous", True) for image in images)
        for item, (_object_name, source) in zip(items, ITEM_SOURCES, strict=True):
            assert item.setProperty("icon", source)
        assert _wait_for(provider.request_started.is_set)
        assert _wait_for(lambda: _all_status(images, "Loading"))
        loading_image = _stable_window_image(window)
        loading_layers = _layer_states(images)
        loading_objects = len(window.findChildren(QObject))

        provider.release_requests.set()
        assert _wait_for(lambda: _all_status(images, "Ready"))
        first_ready_image = window.grabWindow()
        assert not first_ready_image.isNull()
        ready_image = _stable_window_image(window)
        ready_layers = _layer_states(images)
        ready_objects = len(window.findChildren(QObject))

        for item, source in zip(items, ERROR_SOURCES, strict=True):
            assert item.setProperty("icon", source)
        assert _wait_for(lambda: _all_status(images, "Error"))
        error_image = _stable_window_image(window)
        error_layers = _layer_states(images)
        error_objects = len(window.findChildren(QObject))

        print(
            "NAVIGATION_ICON_LAYERS",
            "hashes="
            f"{_image_hash(loading_image)}/{_image_hash(ready_image)}/"
            f"{_image_hash(error_image)}",
            f"layers={loading_layers}/{ready_layers}/{error_layers}",
            f"objects={loading_objects}/{ready_objects}/{error_objects}",
        )

        assert loading_layers == (False, False, False, False)
        assert ready_layers == (True, True, True, True)
        assert error_layers == (False, False, False, False)
        assert first_ready_image == ready_image
        assert error_image == loading_image
        assert loading_objects == ready_objects == error_objects
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(
            qapp, engine, component, window, provider, previous_handler
        )
        assert _new_visible_windows(windows_before) == []

    assert warnings == [
        warning
        for warning in warnings
        if any(source in warning for source in ERROR_SOURCES)
    ]
    qt_failures = _qt_failures(messages)
    assert qt_failures == [
        message
        for message in qt_failures
        if any(source in message for source in ERROR_SOURCES)
    ]
