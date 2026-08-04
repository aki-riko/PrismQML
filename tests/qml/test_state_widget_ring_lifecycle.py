# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""StateWidget ring lifecycle regressions. StateWidget 圆环生命周期回归。"""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
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
    / "feedback"
    / "State"
    / "StateWidget.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "state-widget-ring-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int resultType: Enums.state.type_result

    width: 320
    height: 240
    visible: true
    color: Enums.backgroundColor

    StateWidget {
        objectName: "stateWidget"
        anchors.centerIn: parent
        width: 260
        height: 180
        severity: "success"
        title: "State"
        description: "Lifecycle"
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
    raise AssertionError("StateWidget frame did not stabilize within 600 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _rings(widget: QQuickItem) -> list[QQuickItem]:
    return [
        child
        for child in widget.findChildren(QObject)
        if isinstance(child, QQuickItem)
        and child.metaObject().className().startswith("ProgressRing_")
    ]


def _ring(widget: QQuickItem) -> QQuickItem | None:
    rings = _rings(widget)
    assert len(rings) <= 1, [ring.metaObject().className() for ring in rings]
    return rings[0] if rings else None


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
    widget = window.findChild(QQuickItem, "stateWidget")
    assert widget is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, widget, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _enter_paused_loading(widget: QQuickItem) -> QQuickItem:
    assert widget.setProperty("severity", "loading")
    ring = _ring(widget)
    assert ring is not None
    assert ring.setProperty("paused", True)
    return ring


def test_state_widget_preserves_first_and_repeated_loading_frames(qapp):
    """Lazy candidates must preserve state pixels and first loading frames.

    懒加载候选必须保持状态像素和首次加载帧。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, widget, warnings = _create_scene()
    try:
        result_type = window.property("resultType")
        no_data_image = _stable_window_image(window)
        no_data_ring = _ring(widget)
        no_data_objects = len(widget.findChildren(QObject))

        assert widget.setProperty("stateType", result_type)
        success_image = _stable_window_image(window)
        success_ring = _ring(widget)
        success_objects = len(widget.findChildren(QObject))

        first_loading_ring = _enter_paused_loading(widget)
        first_loading_image = window.grabWindow()
        assert not first_loading_image.isNull()
        loading_image = _stable_window_image(window)
        loading_objects = len(widget.findChildren(QObject))

        assert widget.setProperty("severity", "success")
        restored_success_image = _stable_window_image(window)
        restored_success_ring = _ring(widget)
        restored_success_objects = len(widget.findChildren(QObject))

        second_loading_ring = _enter_paused_loading(widget)
        first_repeated_loading_image = window.grabWindow()
        assert not first_repeated_loading_image.isNull()
        repeated_loading_image = _stable_window_image(window)
        repeated_loading_objects = len(widget.findChildren(QObject))

        print(
            "STATE_WIDGET_RING",
            "hashes="
            f"{_image_hash(no_data_image)}/{_image_hash(success_image)}/"
            f"{_image_hash(first_loading_image)}/{_image_hash(loading_image)}/"
            f"{_image_hash(restored_success_image)}/"
            f"{_image_hash(first_repeated_loading_image)}/"
            f"{_image_hash(repeated_loading_image)}",
            "rings="
            f"{int(no_data_ring is not None)}/{int(success_ring is not None)}/"
            f"{len(_rings(widget))}/{int(restored_success_ring is not None)}",
            "objects="
            f"{no_data_objects}/{success_objects}/{loading_objects}/"
            f"{restored_success_objects}/{repeated_loading_objects}",
        )

        assert no_data_ring is success_ring is first_loading_ring
        assert first_loading_ring is restored_success_ring is second_loading_ring
        assert no_data_objects == success_objects == restored_success_objects
        assert loading_objects == repeated_loading_objects
        assert first_loading_image == loading_image
        assert first_repeated_loading_image == repeated_loading_image == loading_image
        assert restored_success_image == success_image
        assert no_data_image != success_image
        assert loading_image != success_image
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_state_widget_source_keeps_direct_progress_ring():
    """The baseline keeps one direct hidden ring. 基线保留一个直接创建的隐藏圆环。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "ProgressRing {" in source
    assert "visible: _isResultType && severity === \"loading\"" in source
    assert "sourceComponent: ProgressRing {" not in source
