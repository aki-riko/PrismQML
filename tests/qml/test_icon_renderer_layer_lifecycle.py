# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared icon renderer layer regressions. 共享图标渲染层回归。"""

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
    str(ROOT / "tests" / "qml" / "icon-renderer-layer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 220
    height: 140
    visible: true
    color: Enums.backgroundColor

    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.xl

        Icon {
            objectName: "svgIcon"
            iconSize: 64
            color: Enums.accentColor
        }

        Icon {
            objectName: "avatarIcon"
            iconSize: 64
        }
    }
}
"""
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


class _BlockingIconProvider(QQuickImageProvider):
    """Hold asynchronous icon requests at Loading. 异步图标请求保持在加载态。"""

    def __init__(self):
        self.block_requests = os.name == "nt"
        if self.block_requests:
            super().__init__(
                QQuickImageProvider.ImageType.Image,
                QQuickImageProvider.Flag.ForceAsynchronousImageLoading,
            )
        else:
            super().__init__(QQuickImageProvider.ImageType.Image)
        self.request_started = Event()
        self.release_requests = Event()

    def requestImage(self, provider_id: str, size: QSize, requested_size: QSize):
        """Return deterministic opaque pixels after release. 放行后返回确定性像素。"""
        del requested_size
        self.request_started.set()
        if self.block_requests and not self.release_requests.wait(timeout=2):
            return QImage()
        if provider_id.startswith("error"):
            return QImage()
        image = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0xFF2060A0 if provider_id.endswith(".svg") else 0xFFD09030)
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
        _pump(20)
    raise AssertionError("Icon renderer frame did not stabilize within 600 ms")


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


def _image_item(icon: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(icon)
        if item.metaObject().className() == "QQuickImage"
    ]
    assert len(matches) == 1, [
        (item.metaObject().className(), item.objectName())
        for item in _visual_descendants(icon)
    ]
    return matches[0]


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
    provider = _BlockingIconProvider()
    engine.addImageProvider("iconprobe", provider)
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
    svg_icon = window.findChild(QQuickItem, "svgIcon")
    avatar_icon = window.findChild(QQuickItem, "avatarIcon")
    assert svg_icon is not None and avatar_icon is not None
    assert _wait_for(window.isExposed)
    return (
        engine,
        component,
        window,
        svg_icon,
        avatar_icon,
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


def test_async_icon_renderers_preserve_loading_and_first_ready_frames(qapp):
    """Shared SVG and avatar renderers must preserve their first Ready frame.

    共享 SVG 与头像渲染器必须保持首个就绪帧。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        svg_icon,
        avatar_icon,
        provider,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        capture_pixels = os.name == "nt"
        empty_image = (
            _stable_window_image(window) if capture_pixels else QImage()
        )

        svg_icon.setProperty("icon", "image://iconprobe/icon.svg")
        avatar_icon.setProperty("icon", "image://iconprobe/avatar.png")
        assert _wait_for(provider.request_started.is_set)
        assert _wait_for(
            lambda: len(_visual_descendants(svg_icon)) > 1
            and len(_visual_descendants(avatar_icon)) > 1
        )
        svg_image = _image_item(svg_icon)
        avatar_image = _image_item(avatar_icon)
        if capture_pixels:
            assert _evaluate(svg_image, "status === Image.Loading") is True
            assert _evaluate(avatar_image, "status === Image.Loading") is True
        else:
            assert _wait_for(
                lambda: _evaluate(svg_image, "status === Image.Ready")
                and _evaluate(avatar_image, "status === Image.Ready")
            )
        loading_layers = (
            QQmlProperty(svg_image, "layer.enabled").read(),
            QQmlProperty(avatar_image, "layer.enabled").read(),
        )
        loading_objects = len(window.findChildren(QObject))

        provider.release_requests.set()
        assert _wait_for(
            lambda: _evaluate(svg_image, "status === Image.Ready")
            and _evaluate(avatar_image, "status === Image.Ready")
        )
        first_ready_image = QImage()
        ready_image = QImage()
        if capture_pixels:
            first_ready_image = window.grabWindow()
            assert not first_ready_image.isNull()
            ready_image = _stable_window_image(window)
        ready_layers = (
            QQmlProperty(svg_image, "layer.enabled").read(),
            QQmlProperty(avatar_image, "layer.enabled").read(),
        )
        ready_objects = len(window.findChildren(QObject))

        svg_icon.setProperty("icon", "image://iconprobe/error.svg")
        avatar_icon.setProperty("icon", "image://iconprobe/error.png")
        assert _wait_for(
            lambda: _evaluate(svg_image, "status === Image.Error")
            and _evaluate(avatar_image, "status === Image.Error")
        )
        error_image = (
            _stable_window_image(window) if capture_pixels else QImage()
        )
        error_layers = (
            QQmlProperty(svg_image, "layer.enabled").read(),
            QQmlProperty(avatar_image, "layer.enabled").read(),
        )
        error_objects = len(window.findChildren(QObject))

        pixel_hashes = "not-captured"
        if capture_pixels:
            pixel_hashes = (
                f"{_image_hash(empty_image)}/{_image_hash(ready_image)}/"
                f"{_image_hash(error_image)}"
            )
        print(
            "ICON_RENDERER_LAYERS",
            f"hashes={pixel_hashes}",
            f"layers={loading_layers}/{ready_layers}/{error_layers}",
            f"objects={loading_objects}/{ready_objects}/{error_objects}",
        )

        if capture_pixels:
            assert loading_layers == (False, False)
        else:
            assert loading_layers == (True, True)
        assert ready_layers == (True, True)
        assert error_layers == (False, False)
        assert loading_objects == ready_objects == error_objects
        if capture_pixels:
            assert first_ready_image == ready_image
            assert error_image == empty_image
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(
            qapp, engine, component, window, provider, previous_handler
        )
        assert _new_visible_windows(windows_before) == []

    expected_errors = (
        "Failed to get image from provider: image://iconprobe/error.svg",
        "Failed to get image from provider: image://iconprobe/error.png",
    )
    assert warnings == [
        warning
        for warning in warnings
        if any(expected in warning for expected in expected_errors)
    ]
    qt_failures = _qt_failures(messages)
    assert qt_failures == [
        message
        for message in qt_failures
        if any(expected in message for expected in expected_errors)
    ]
