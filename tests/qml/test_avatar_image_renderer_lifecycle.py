# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Avatar image renderer lifecycle regressions. Avatar 图片渲染器生命周期回归。"""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "avatar-image-renderer-lifecycle.qml")
)
AVATAR_SOURCE = QUrl.fromLocalFile(
    str(ROOT / "examples" / "resources" / "image" / "avatar" / "avatar.png")
).toString()
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 180
    height: 160
    visible: true
    color: Enums.backgroundColor

    Avatar {
        objectName: "avatar"
        anchors.centerIn: parent
        size: 80
        text: "K"
    }
}
"""


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
    raise AssertionError("Avatar frame did not stabilize within 600 ms")


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


def _renderer_items(avatar: QQuickItem) -> tuple[list[QQuickItem], list[QQuickItem]]:
    descendants = _visual_descendants(avatar)
    avatar_source = str(avatar.property("source"))
    images = [
        item
        for item in descendants
        if item.metaObject().indexOfProperty("fillMode") >= 0
        and item.property("source").toString() == avatar_source
    ]
    canvases = [
        item
        for item in descendants
        if item.metaObject().indexOfProperty("renderTarget") >= 0
        and item.metaObject().indexOfProperty("renderStrategy") >= 0
    ]
    return images, canvases


def _image_ready(image: QQuickItem) -> bool:
    expression = QQmlExpression(
        QQmlEngine.contextForObject(image), image, "status === Image.Ready"
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return bool(result)


def _renderer_counts(avatar: QQuickItem) -> tuple[int, int]:
    images, canvases = _renderer_items(avatar)
    return len(images), len(canvases)


def _placeholder_renderer_count(avatar: QQuickItem) -> int:
    icons = [
        item
        for item in _visual_descendants(avatar)
        if item.metaObject().indexOfProperty("isImageIcon") >= 0
        and item.metaObject().indexOfProperty("iconSize") >= 0
    ]
    assert len(icons) == 1
    return sum(
        item.metaObject().indexOfProperty("fillMode") >= 0
        for item in _visual_descendants(icons[0])
    )


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
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
    avatar = window.findChild(QQuickItem, "avatar")
    assert avatar is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, avatar, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_avatar_preserves_first_and_repeated_image_frames(qapp):
    """Image renderer must preserve first and repeated source frames.

    图片渲染器必须保持首次与重复设置来源的帧。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, avatar, warnings = _create_scene()
    try:
        text_image = _stable_window_image(window)
        text_renderers = _renderer_counts(avatar)
        text_placeholder_renderers = _placeholder_renderer_count(avatar)
        text_objects = len(window.findChildren(QObject))
        source_images, avatar_canvases = _renderer_items(avatar)
        assert len(source_images) == len(avatar_canvases) == 1
        source_image = source_images[0]
        canvas_painted = QSignalSpy(avatar_canvases[0].painted)

        assert avatar.setProperty("source", AVATAR_SOURCE)
        assert _wait_for(
            lambda: _renderer_counts(avatar) == (1, 1)
        ), (
            text_renderers,
            _renderer_counts(avatar),
            [
                item.metaObject().className()
                for item in _visual_descendants(avatar)
            ],
        )
        assert _wait_for(lambda: _image_ready(source_image))
        assert _wait_for(lambda: canvas_painted.count() >= 1)
        first_ready_image = window.grabWindow()
        assert not first_ready_image.isNull()
        ready_image = _stable_window_image(window)
        ready_renderers = _renderer_counts(avatar)
        ready_placeholder_renderers = _placeholder_renderer_count(avatar)
        ready_objects = len(window.findChildren(QObject))

        assert avatar.setProperty("source", "")
        restored_text_image = _stable_window_image(window)
        cleared_renderers = _renderer_counts(avatar)
        cleared_placeholder_renderers = _placeholder_renderer_count(avatar)
        cleared_objects = len(window.findChildren(QObject))

        painted_count = canvas_painted.count()
        assert avatar.setProperty("source", AVATAR_SOURCE)
        assert _wait_for(lambda: _image_ready(source_image))
        assert _wait_for(lambda: canvas_painted.count() > painted_count)
        first_restored_image = window.grabWindow()
        assert not first_restored_image.isNull()
        restored_ready_image = _stable_window_image(window)
        restored_renderers = _renderer_counts(avatar)
        restored_placeholder_renderers = _placeholder_renderer_count(avatar)
        restored_objects = len(window.findChildren(QObject))

        assert avatar.setProperty("source", "")
        assert avatar.setProperty("text", "")
        assert _wait_for(lambda: _placeholder_renderer_count(avatar) == 1)
        first_default_image = window.grabWindow()
        assert not first_default_image.isNull()
        default_image = _stable_window_image(window)
        default_placeholder_renderers = _placeholder_renderer_count(avatar)
        default_objects = len(window.findChildren(QObject))

        assert avatar.setProperty("text", "K")
        restored_text_again_image = _stable_window_image(window)
        restored_text_placeholder_renderers = _placeholder_renderer_count(avatar)
        restored_text_objects = len(window.findChildren(QObject))

        print(
            "AVATAR_IMAGE_RENDERER",
            "hashes="
            f"{_image_hash(text_image)}/{_image_hash(first_ready_image)}/"
            f"{_image_hash(ready_image)}/{_image_hash(restored_text_image)}/"
            f"{_image_hash(first_restored_image)}/"
            f"{_image_hash(restored_ready_image)}/"
            f"{_image_hash(first_default_image)}/{_image_hash(default_image)}/"
            f"{_image_hash(restored_text_again_image)}",
            "renderers="
            f"{text_renderers}/{ready_renderers}/{cleared_renderers}/"
            f"{restored_renderers}",
            "placeholders="
            f"{text_placeholder_renderers}/{ready_placeholder_renderers}/"
            f"{cleared_placeholder_renderers}/"
            f"{restored_placeholder_renderers}/"
            f"{default_placeholder_renderers}/"
            f"{restored_text_placeholder_renderers}",
            "objects="
            f"{text_objects}/{ready_objects}/{cleared_objects}/{restored_objects}/"
            f"{default_objects}/{restored_text_objects}",
        )

        assert text_placeholder_renderers == 0
        assert ready_placeholder_renderers == 1
        assert cleared_placeholder_renderers == 0
        assert restored_placeholder_renderers == 1
        assert default_placeholder_renderers == 1
        assert restored_text_placeholder_renderers == 0
        assert text_objects < default_objects
        assert cleared_objects < default_objects
        assert restored_text_objects < default_objects
        assert ready_objects == restored_objects == default_objects
        assert first_ready_image == ready_image
        assert first_restored_image == restored_ready_image
        assert first_default_image == default_image
        assert ready_image != text_image
        assert restored_text_image == text_image
        assert restored_ready_image == ready_image
        assert default_image != text_image
        assert restored_text_again_image == text_image
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []
