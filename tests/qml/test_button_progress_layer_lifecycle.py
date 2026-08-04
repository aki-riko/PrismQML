# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Button progress layer lifecycle regressions. 按钮进度层生命周期回归。"""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "button-progress-layer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int indeterminateFeature: Enums.button.feature_indeterminate_bar

    width: 320
    height: 120
    visible: true
    color: Enums.backgroundColor

    Button {
        id: progressButton

        objectName: "progressButton"
        anchors.centerIn: parent
        width: 240
        height: Enums.controlSize.buttonHeight
        text: "Progress"
        style: Enums.button.style_primary
        feature: Enums.button.feature_progress_bar
        progress: 0.6
        showProgress: false
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
    raise AssertionError("Button progress frame did not stabilize within 600 ms")


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


def _has_properties(item: QQuickItem, *names: str) -> bool:
    meta = item.metaObject()
    return all(meta.indexOfProperty(name) >= 0 for name in names)


def _progress_layers(button: QQuickItem) -> tuple[QQuickItem, QQuickItem]:
    progress_modules = [
        item
        for item in _visual_descendants(button)
        if _has_properties(item, "_progressColor", "showProgress", "progress")
    ]
    assert len(progress_modules) == 1
    progress_content = progress_modules[0].parentItem()
    assert progress_content is not None
    progress_shell = progress_content.parentItem()
    assert progress_shell is not None
    mask_candidates = [
        item
        for item in progress_shell.childItems()
        if item is not progress_content
        and item.metaObject().className().startswith("QQuickRectangle")
        and not item.isVisible()
    ]
    assert len(mask_candidates) == 1
    progress_mask = mask_candidates[0]
    assert QQmlProperty(progress_mask, "layer.enabled").isValid()
    assert QQmlProperty(progress_content, "layer.enabled").isValid()
    return progress_mask, progress_content


def _layer_states(*items: QQuickItem) -> tuple[bool, ...]:
    return tuple(bool(QQmlProperty(item, "layer.enabled").read()) for item in items)


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
    button = window.findChild(QQuickItem, "progressButton")
    assert button is not None
    assert _wait_for(window.isExposed)
    assert _wait_for(
        lambda: any(
            _has_properties(item, "_progressColor", "showProgress", "progress")
            for item in _visual_descendants(button)
        )
    )
    return engine, component, window, button, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_button_progress_layers_preserve_first_visible_frame(qapp):
    """Toggling progress must preserve its first visible frame. 切换进度须保持首个可见帧。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, button, warnings = _create_scene()
    try:
        layers = _progress_layers(button)
        initial_geometry = (button.x(), button.y(), button.width(), button.height())
        hidden_image = _stable_window_image(window)
        hidden_layers = _layer_states(*layers)
        hidden_objects = len(window.findChildren(QObject))

        assert button.setProperty("showProgress", True)
        first_visible_image = window.grabWindow()
        assert not first_visible_image.isNull()
        visible_image = _stable_window_image(window)
        visible_layers = _layer_states(*layers)
        visible_objects = len(window.findChildren(QObject))

        assert button.setProperty("showProgress", False)
        restored_hidden_image = _stable_window_image(window)
        restored_hidden_layers = _layer_states(*layers)
        restored_hidden_objects = len(window.findChildren(QObject))

        assert button.setProperty("showProgress", True)
        first_restored_image = window.grabWindow()
        assert not first_restored_image.isNull()
        restored_visible_image = _stable_window_image(window)
        restored_visible_layers = _layer_states(*layers)
        restored_visible_objects = len(window.findChildren(QObject))

        assert button.setProperty("showProgress", False)
        assert button.setProperty(
            "feature", window.property("indeterminateFeature")
        )
        indeterminate_layers = _layer_states(*layers)

        print(
            "BUTTON_PROGRESS_LAYERS",
            "hashes="
            f"{_image_hash(hidden_image)}/{_image_hash(visible_image)}/"
            f"{_image_hash(restored_hidden_image)}/"
            f"{_image_hash(restored_visible_image)}",
            "layers="
            f"{hidden_layers}/{visible_layers}/{restored_hidden_layers}/"
            f"{restored_visible_layers}/{indeterminate_layers}",
            "objects="
            f"{hidden_objects}/{visible_objects}/{restored_hidden_objects}/"
            f"{restored_visible_objects}",
        )

        assert hidden_layers == (False, False)
        assert visible_layers == (True, True)
        assert restored_hidden_layers == (False, False)
        assert restored_visible_layers == (True, True)
        assert indeterminate_layers == (True, True)
        assert first_visible_image == visible_image
        assert first_restored_image == restored_visible_image
        assert restored_hidden_image == hidden_image
        assert restored_visible_image == visible_image
        assert (
            hidden_objects
            == visible_objects
            == restored_hidden_objects
            == restored_visible_objects
        )
        assert initial_geometry == (
            button.x(),
            button.y(),
            button.width(),
            button.height(),
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []
