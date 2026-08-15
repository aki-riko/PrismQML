# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBox mask layer lifecycle regressions. ComboBox 遮罩图层生命周期回归。"""

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
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ComboBox"
    / "_internal"
    / "ComboBoxCoreContent.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-mask-layer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 240
    height: 140
    visible: true
    color: Enums.backgroundColor

    ComboBoxCore {
        objectName: "combo"
        x: 30
        y: 50
        width: 180
        model: ["Alpha", "Beta", "Gamma"]
        currentIndex: 0
        style: Enums.comboBox.style_primary
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
    raise AssertionError("ComboBox frame did not stabilize within 600 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _combo_content(combo: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in combo.childItems()
        if item.metaObject().className().startswith("ComboBoxCoreContent")
    ]
    assert len(matches) == 1
    return matches[0]


def _enabled_direct_layers(combo: QQuickItem) -> list[QQuickItem]:
    enabled = []
    for item in _combo_content(combo).childItems():
        layer_enabled = QQmlProperty(item, "layer.enabled")
        if layer_enabled.isValid() and bool(layer_enabled.read()):
            enabled.append(item)
    return enabled


def _layer_names(combo: QQuickItem) -> list[str]:
    return [item.metaObject().className() for item in _enabled_direct_layers(combo)]


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
    combo = window.findChild(QQuickItem, "combo")
    assert combo is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, combo, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_combo_box_preserves_square_and_restored_frames(qapp):
    """Radius changes must preserve first frames and restore exact pixels.

    圆角切换必须保持首帧，并在恢复后还原完全一致的像素。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, combo, warnings = _create_scene()
    try:
        default_radius = combo.property("radius")
        assert default_radius > 0
        default_geometry = (
            combo.x(),
            combo.y(),
            combo.width(),
            combo.height(),
        )
        default_image = _stable_window_image(window)
        default_layers = len(_enabled_direct_layers(combo))
        default_objects = len(window.findChildren(QObject))

        assert combo.setProperty("radius", 0)
        first_square_image = window.grabWindow()
        assert not first_square_image.isNull()
        square_image = _stable_window_image(window)
        square_layers = len(_enabled_direct_layers(combo))
        square_objects = len(window.findChildren(QObject))

        assert combo.setProperty("radius", default_radius)
        first_restored_image = window.grabWindow()
        assert not first_restored_image.isNull()
        restored_image = _stable_window_image(window)
        restored_layers = len(_enabled_direct_layers(combo))
        restored_objects = len(window.findChildren(QObject))

        print(
            "COMBO_BOX_MASK_LAYER",
            "hashes="
            f"{_image_hash(default_image)}/{_image_hash(first_square_image)}/"
            f"{_image_hash(square_image)}/{_image_hash(first_restored_image)}/"
            f"{_image_hash(restored_image)}",
            f"layers={default_layers}/{square_layers}/{restored_layers}",
            f"objects={default_objects}/{square_objects}/{restored_objects}",
            f"enabled={_layer_names(combo)}",
        )

        assert (default_layers, square_layers, restored_layers) == (1, 1, 1)
        assert default_objects == square_objects == restored_objects
        assert first_square_image == square_image
        assert first_restored_image == restored_image == default_image
        assert square_image == default_image
        assert default_geometry == (
            combo.x(),
            combo.y(),
            combo.width(),
            combo.height(),
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_combo_box_source_keeps_mask_layer_enabled():
    """The content owner keeps the background mask layer enabled. 内容所有者保持背景遮罩图层启用。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "layer.enabled: true" in source
